from cereal import log
from common.swaglog import cloudlog
from openpilot.common.conversions import Conversions as CV
from openpilot.common.params import Params
from openpilot.common.realtime import DT_MDL
from openpilot.selfdrive.controls.lib.drive_helpers import get_road_edge
from openpilot.selfdrive.modeld.custom_model_metadata import CustomModelMetadata, ModelCapabilities
from sicuem.adelantamiento import should_start_overtake, get_overtake_command
import cereal.messaging as messaging  # Asegúrate de que ya está importado
from openpilot.selfdrive.controls.lib.drive_helpers import VCruiseHelper
from cereal import car, log, custom

import time
from cereal import log

LaneChangeState = log.LaneChangeState
LaneChangeDirection = log.LaneChangeDirection

LANE_CHANGE_SPEED_MIN = 20 * CV.MPH_TO_MS
LANE_CHANGE_TIME_MAX = 10.

DESIRES = {
  LaneChangeDirection.none: {
    LaneChangeState.off: log.Desire.none,
    LaneChangeState.preLaneChange: log.Desire.none,
    LaneChangeState.laneChangeStarting: log.Desire.none,
    LaneChangeState.laneChangeFinishing: log.Desire.none,
  },
  LaneChangeDirection.left: {
    LaneChangeState.off: log.Desire.none,
    LaneChangeState.preLaneChange: log.Desire.none,
    LaneChangeState.laneChangeStarting: log.Desire.laneChangeLeft,
    LaneChangeState.laneChangeFinishing: log.Desire.laneChangeLeft,
  },
  LaneChangeDirection.right: {
    LaneChangeState.off: log.Desire.none,
    LaneChangeState.preLaneChange: log.Desire.none,
    LaneChangeState.laneChangeStarting: log.Desire.laneChangeRight,
    LaneChangeState.laneChangeFinishing: log.Desire.laneChangeRight,
  },
}

AUTO_LANE_CHANGE_TIMER = {
  -1: 0.0,
  0: 0.0,
  1: 0.1,
  2: 0.5,
  3: 1.0,
  4: 1.5,
}

def get_min_lateral_speed(value: int, is_metric: bool, default: float = LANE_CHANGE_SPEED_MIN):
  speed: float = default if value == 0 else value * CV.KPH_TO_MS if is_metric else CV.MPH_TO_MS
  return speed

class DesireHelper:
  def __init__(self):
    self.lane_change_state = LaneChangeState.off
    self.lane_change_direction = LaneChangeDirection.none
    self.lane_change_timer = 0.0
    self.lane_change_ll_prob = 1.0
    self.keep_pulse_timer = 0.0
    self.prev_one_blinker = False
    self.desire = log.Desire.none
    self.sm = messaging.SubMaster(['carControl', 'radarState'])
    self.param_s = Params()
    self.lane_change_wait_timer = 0
    self.prev_lane_change = False
    self.prev_brake_pressed = False
    self.road_edge = False
    self.param_read_counter = 0
    self.edge_toggle = self.param_s.get_bool("RoadEdge")
    self.lane_change_set_timer = int(self.param_s.get("AutoLaneChangeTimer", encoding="utf8"))
    self.lane_change_bsm_delay = self.param_s.get_bool("AutoLaneChangeBsmDelay")

    self.custom_model_metadata = CustomModelMetadata(params=self.param_s, init_only=True)
    self.model_use_lateral_planner = self.custom_model_metadata.valid and \
                                     self.custom_model_metadata.capabilities & ModelCapabilities.LateralPlannerSolution

    self.overtake_active = False
    self.overtake_timer = 0.0
    self.overtake_speed_delta = 0.0
    self.overtake_v_cruise_last = None
    self.params = Params()
    self.original_set_speed=0

    self.CP = messaging.log_from_bytes(self.params.get("CarParams", block=True), car.CarParams)

      # Uses car interface helper functions, altering state won't be considered by card for actuation
    self.speed_increased = False

    self.v_cruise_helper = VCruiseHelper(self.CP)

    controls_state_bytes = self.params.get("ReplayControlsState")
    if controls_state_bytes:
      controls_state = log.ControlsState.from_bytes(controls_state_bytes)
      self.v_cruise_helper.v_cruise_kph = controls_state.vCruise
      # --- NUEVO: inicializar vel_adel con el mismo valor que el setSpeed ---
      self.params.put("vel_adel", str(controls_state.vCruise))  # Guardar en km/h
    else:
      # Si no existe, ponemos un valor seguro por defecto (ej. 30 km/h)
      self.v_cruise_helper.v_cruise_kph = 30
      self.params.put("vel_adel", "30.0")

  def read_param(self):
    self.edge_toggle = self.param_s.get_bool("RoadEdge")
    self.lane_change_set_timer = int(self.param_s.get("AutoLaneChangeTimer", encoding="utf8"))
    self.lane_change_bsm_delay = self.param_s.get_bool("AutoLaneChangeBsmDelay")

  def check_and_force_lane_change_param(self, carstate):
    if not self.param_s.get_bool("c_carril") or self.lane_change_state != LaneChangeState.off:
      return

    # Izquierda
    if self.param_s.get_bool("ForceLaneChangeLeft"):
      self.param_s.put_bool("ForceLaneChangeLeft", False)
      if carstate.leftBlindspot:
        #cloudlog.warning("🔴 Cambio a izquierda bloqueado por ángulo muerto")
        return
      self.lane_change_direction = LaneChangeDirection.left
      self.lane_change_state = LaneChangeState.laneChangeStarting
      self.lane_change_ll_prob = 1.0
      self.lane_change_wait_timer = 0
      #cloudlog.info("⬅️ Cambio de carril forzado a la izquierda")
      return

    # Derecha
    if self.param_s.get_bool("ForceLaneChangeRight"):
      self.param_s.put_bool("ForceLaneChangeRight", False)
      if carstate.rightBlindspot:
        #cloudlog.warning("🔴 Cambio a derecha bloqueado por ángulo muerto")
        return
      self.lane_change_direction = LaneChangeDirection.right
      self.lane_change_state = LaneChangeState.laneChangeStarting
      self.lane_change_ll_prob = 1.0
      self.lane_change_wait_timer = 0
      #cloudlog.info("➡️ Cambio de carril forzado a la derecha")



  def auto_overtake_with_bsm(self, carstate, d_rel, v_rel, lead_status):
    try:
      params = Params()
      params.put_bool("overtakingActive", self.overtake_active)
      params.put_bool("waitingToReturn", self.overtake_active and self.overtake_timer > 5.0 and not carstate.rightBlindspot)
      params.put_bool("returningRight", self.overtake_timer > 10.0 and not carstate.rightBlindspot)

      if not self.overtake_active and lead_status:
        distancia_ok = d_rel < 50.0
        velocidad_ok = (carstate.cruiseSpeed - carstate.vEgo) > 10.0  # 36 km/h

        if distancia_ok and velocidad_ok:
          self.lane_change_direction = LaneChangeDirection.left
          self.lane_change_state = LaneChangeState.laneChangeStarting
          self.lane_change_ll_prob = 1.0
          self.lane_change_wait_timer = 0
          self.overtake_active = True
          self.overtake_timer = 0.0
          self.overtake_v_cruise_last = carstate.cruiseSpeed
          self.overtake_speed_delta = 10.0  # m/s ≈ +36 km/h
          params.put("OverrideCruiseSpeed", str(self.overtake_v_cruise_last + self.overtake_speed_delta))
          cloudlog.info("🟢 Adelantamiento automático (con BSM) activado (+36 km/h)")

      elif self.overtake_active:
        self.overtake_timer += DT_MDL
        if self.overtake_timer > 10.0:
          if not carstate.rightBlindspot:
            self.lane_change_direction = LaneChangeDirection.right
            self.lane_change_state = LaneChangeState.laneChangeStarting
            cloudlog.info("🔄 Retorno automático al carril derecho tras 10s y sin BSM")
          self.overtake_active = False
          if self.overtake_v_cruise_last is not None:
            params.put("OverrideCruiseSpeed", str(self.overtake_v_cruise_last))
            cloudlog.info("✅ Restablecida velocidad original tras adelantamiento")

    except Exception as e:
      cloudlog.error(f"❌ Error en lógica de adelantamiento (con BSM): {e}")

  # ---------------------------------------------------------------------------------
  # Función: auto_overtake_without_bsm
  # Descripción:
  #   - Detecta si vamos al menos 15 km/h más lentos que la velocidad de referencia
  #     (set_speed - vEgo > 15 km/h) y el vehículo delantero está a menos de 50 m.
  #   - Si se cumplen estas condiciones, inicia un cambio de carril a la izquierda
  #     (adelantamiento) y aumenta la velocidad objetivo en +10 km/h.
  #   - Permanece en el carril izquierdo durante 15 segundos.
  #   - Tras ese tiempo, si no hay impedimentos, inicia el cambio de carril a la derecha
  #     para regresar al carril original.
  #   - Usa variables internas para controlar el estado del adelantamiento y evitar
  #     activaciones múltiples simultáneas.
  # ---------------------------------------------------------------------------------

  def auto_overtake_without_bsm(self, carstate, v_rel, d_rel, set_speed, lead_status):
    try:
      # Inicializamos variables internas si no existen
      if not hasattr(self, "overtake_active"):
        self.overtake_active = False
        self.overtake_start_time = 0
        self.speed_increased = False  # <-- flag para subir velocidad solo una vez

      # --- INICIAR ADELANTAMIENTO ---
      if lead_status and not self.overtake_active:
        velocidad_ok = (set_speed - carstate.vEgo) > 4.166  # 15 km/h
        distancia_ok = d_rel < 50.0

        if velocidad_ok and distancia_ok:
        #if True:

          # Guardar la velocidad inicial SOLO si no hay otro adelantamiento activo
          if not self.overtake_active:
            self.original_set_speed = set_speed
            self.params.put("vel_adel", str(self.original_set_speed * 3.6))  # Guardar en km/h

          # Iniciar adelantamiento → cambio a la izquierda
          self.lane_change_direction = LaneChangeDirection.left
          self.lane_change_state = LaneChangeState.laneChangeStarting
          self.lane_change_ll_prob = 1.0
          self.lane_change_wait_timer = 0
          self.overtake_active = True
          self.overtake_start_time = time.time()
          self.speed_increased = False  # Reiniciar el flag
          cloudlog.info(
            f"🟢 Adelantamiento iniciado: cambio a carril izquierdo. Velocidad base: {self.original_set_speed * 3.6:.1f} km/h"
          )

      # --- MIENTRAS ADELANTA ---
      elif self.overtake_active:
        elapsed = time.time() - self.overtake_start_time

        # Subir velocidad +10 km/h solo una vez
        # Subir velocidad +15 km/h solo una vez
        if not self.speed_increased:
          new_speed = (self.original_set_speed * 3.6) + 15
          self.params.put("vel_adel", str(new_speed))
          self.v_cruise_helper.v_cruise_kph = new_speed  # <--- Ajustar control de crucero real
          self.speed_increased = True
          cloudlog.info(f"⬆️ Velocidad incrementada +15 km/h: {new_speed:.1f} km/h")

        # Si han pasado 15s → volver al carril derecho
        if elapsed >= 15:
          self.lane_change_direction = LaneChangeDirection.right
          self.lane_change_state = LaneChangeState.laneChangeStarting
          self.lane_change_ll_prob = 1.0
          self.lane_change_wait_timer = 0
          self.overtake_active = False

          # Restaurar velocidad original
          self.params.put("vel_adel", str(self.original_set_speed * 3.6))
          self.v_cruise_helper.v_cruise_kph = self.original_set_speed * 3.6  # <--- Restaurar
          cloudlog.info(
            f"🔵 Adelantamiento completado: retorno al carril derecho. Velocidad restaurada a {self.original_set_speed * 3.6:.1f} km/h"
          )


    except Exception as e:
      cloudlog.error(f"❌ Error en adelantamiento simple (sin BSM): {e}")

  def update(self, carstate, lateral_active, lane_change_prob, model_data=None, lat_plan_sp=None, desire_override=None,
             radar_state=None):
    self.sm.update()

    try:
      lead = self.sm['radarState'].leadOne
      d_rel = float(lead.dRel)
      v_rel = float(lead.vRel)
      lead_status = lead.status
    except Exception as e:
      d_rel, v_rel, lead_status = 0.0, 0.0, False

    # Obtener datos de carControl-----------------------------------------------------------------------------------------------

    # cambia el set speed
    #self.params.put("vel_adel", str(40))

    try:
      if self.sm.updated['carControl']:
        car_control = self.sm['carControl']
        set_speed = car_control.hudControl.setSpeed
      else:
        set_speed = 0.1
    except Exception as e:
      set_speed = 0.1

    # --- Sincronizar vel_adel si no estamos adelantando ---
    if not self.overtake_active and not self.speed_increased:
      try:
        # Guardar vel_adel como el set_speed actual en km/h
        self.params.put("vel_adel", str(set_speed * 3.6))
      except Exception as e:
        cloudlog.error(f"Error al sincronizar vel_adel: {e}")

    # 👇 Si estamos en adelantamiento, usa el valor de vel_adel en lugar del HUD
    if self.overtake_active or self.speed_increased:
      try:
        vel_adel_str = self.params.get("vel_adel", encoding="utf8")
        if vel_adel_str:
          set_speed = float(vel_adel_str) / 3.6  # lo pasamos a m/s
      except (ValueError, TypeError) as e:
        cloudlog.error(f"Valor inválido en vel_adel: {vel_adel_str}, usando set_speed actual")

    # 📤 Imprimir todos los datos juntos
    '''
    print("📊 DATOS ADELANTAMIENTO:")
    print(f"• 🚘 Lead detectado: {'✅ Sí' if lead_status else '❌ No'}")
    print(f"• 📍 Distancia (d_rel): {d_rel:.1f} m")
    print(f"• 💨 Diferencia velocidad (v_rel): {v_rel:.1f} m/s")
    print(f"• 🚗 setSpeed: {set_speed:.2f} m/s ({set_speed * 3.6:.1f} km/h)")
    '''

    if desire_override is not None:
      self.desire = desire_override
      return

    if self.param_read_counter % 50 == 0:
      self.read_param()
    self.param_read_counter += 1
    lane_change_auto_timer = AUTO_LANE_CHANGE_TIMER.get(self.lane_change_set_timer, 2.0)
    v_ego = carstate.vEgo
    one_blinker = carstate.leftBlinker != carstate.rightBlinker

    if self.param_s.get_bool("sic_adelantar_bsm"):
      #enviar_log("✅ Ha entrado en condicional: sic_adelantar_bsm", nivel="DEBUG", origen="adelantamiento")
      self.auto_overtake_with_bsm(carstate, radar_state)

    elif self.param_s.get_bool("sic_adelantar_nobsm"):
      #enviar_log("✅ Ha entrado en condicional: sic_adelantar_nobsm", nivel="DEBUG", origen="adelantamiento")
      self.auto_overtake_without_bsm(carstate, v_rel, d_rel, set_speed, lead_status)

    else:
      pass
      #enviar_log("⚠️ No se ha activado ningún modo de adelantamiento", nivel="DEBUG", origen="adelantamiento")

    #Cambio de carril (hecho por Adrián)
    self.check_and_force_lane_change_param(carstate)


    # TODO: SP: !659: User-defined minimum lane change speed
    below_lane_change_speed = v_ego < LANE_CHANGE_SPEED_MIN

    if self.model_use_lateral_planner:
      self.road_edge = get_road_edge(carstate, model_data, self.edge_toggle)

    if not lateral_active or self.lane_change_timer > LANE_CHANGE_TIME_MAX or self.lane_change_set_timer == -1:
      self.lane_change_state = LaneChangeState.off
      self.lane_change_direction = LaneChangeDirection.none
      self.prev_lane_change = False
      self.prev_brake_pressed = False
    else:
      # LaneChangeState.off
      if self.lane_change_state == LaneChangeState.off and one_blinker and not self.prev_one_blinker and not below_lane_change_speed:
        self.lane_change_state = LaneChangeState.preLaneChange
        self.lane_change_ll_prob = 1.0
        self.lane_change_wait_timer = 0

      # LaneChangeState.preLaneChange
      elif self.lane_change_state == LaneChangeState.preLaneChange and (self.road_edge if self.model_use_lateral_planner else lat_plan_sp.laneChangeEdgeBlockDEPRECATED):
        self.lane_change_direction = LaneChangeDirection.none
      elif self.lane_change_state == LaneChangeState.preLaneChange:
        # Set lane change direction
        self.lane_change_direction = LaneChangeDirection.left if \
          carstate.leftBlinker else LaneChangeDirection.right

        torque_applied = carstate.steeringPressed and \
                         ((carstate.steeringTorque > 0 and self.lane_change_direction == LaneChangeDirection.left) or
                          (carstate.steeringTorque < 0 and self.lane_change_direction == LaneChangeDirection.right))

        blindspot_detected = ((carstate.leftBlindspot and self.lane_change_direction == LaneChangeDirection.left) or
                              (carstate.rightBlindspot and self.lane_change_direction == LaneChangeDirection.right))

        self.lane_change_wait_timer += DT_MDL

        if self.lane_change_bsm_delay and blindspot_detected and lane_change_auto_timer:
          if lane_change_auto_timer == 0.1:
            self.lane_change_wait_timer = -1
          else:
            self.lane_change_wait_timer = lane_change_auto_timer - 1

        auto_lane_change_allowed = lane_change_auto_timer and self.lane_change_wait_timer > lane_change_auto_timer

        if carstate.brakePressed and not self.prev_brake_pressed:
          self.prev_brake_pressed = carstate.brakePressed

        if not one_blinker or below_lane_change_speed:
          self.lane_change_state = LaneChangeState.off
          self.lane_change_direction = LaneChangeDirection.none
          self.prev_lane_change = False
          self.prev_brake_pressed = False
        elif (torque_applied or (auto_lane_change_allowed and not self.prev_lane_change and not self.prev_brake_pressed)) and \
          not blindspot_detected:
          self.lane_change_state = LaneChangeState.laneChangeStarting
          self.prev_lane_change = True

      # LaneChangeState.laneChangeStarting
      elif self.lane_change_state == LaneChangeState.laneChangeStarting:
        # fade out over .5s
        self.lane_change_ll_prob = max(self.lane_change_ll_prob - 2 * DT_MDL, 0.0)

        # 98% certainty
        if lane_change_prob < 0.02 and self.lane_change_ll_prob < 0.01:
          self.lane_change_state = LaneChangeState.laneChangeFinishing

      # LaneChangeState.laneChangeFinishing
      elif self.lane_change_state == LaneChangeState.laneChangeFinishing:
        # fade in laneline over 1s
        self.lane_change_ll_prob = min(self.lane_change_ll_prob + DT_MDL, 1.0)

        if self.lane_change_ll_prob > 0.99:
          self.lane_change_direction = LaneChangeDirection.none
          if one_blinker:
            self.lane_change_state = LaneChangeState.preLaneChange
          else:
            self.lane_change_state = LaneChangeState.off
            self.prev_lane_change = False
            self.prev_brake_pressed = False

    if self.lane_change_state in (LaneChangeState.off, LaneChangeState.preLaneChange):
      self.lane_change_timer = 0.0
    else:
      self.lane_change_timer += DT_MDL

    self.prev_one_blinker = one_blinker

    self.desire = DESIRES[self.lane_change_direction][self.lane_change_state]

    # Send keep pulse once per second during LaneChangeStart.preLaneChange
    if self.lane_change_state in (LaneChangeState.off, LaneChangeState.laneChangeStarting):
      self.keep_pulse_timer = 0.0
    elif self.lane_change_state == LaneChangeState.preLaneChange:
      self.keep_pulse_timer += DT_MDL
      if self.keep_pulse_timer > 1.0:
        self.keep_pulse_timer = 0.0
      elif self.desire in (log.Desire.keepLeft, log.Desire.keepRight):
        self.desire = log.Desire.none
