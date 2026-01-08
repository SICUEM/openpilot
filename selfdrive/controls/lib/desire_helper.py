from cereal import log
from common.swaglog import cloudlog
from openpilot.common.conversions import Conversions as CV
from openpilot.common.params import Params
from openpilot.common.realtime import DT_MDL
from openpilot.selfdrive.controls.lib.drive_helpers import get_road_edge
from openpilot.selfdrive.modeld.custom_model_metadata import CustomModelMetadata, ModelCapabilities
from sicuem.adelantamiento import should_start_overtake, get_overtake_command
from sicuem.adripilot.log_mqtt import enviar_log
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

  def _has_bsm(self, carstate):
    """Verifica de forma segura si el coche tiene BSM disponible."""
    try:
      # Intentar acceder a los atributos de BSM
      # Si no existen o hay error, asumimos que no hay BSM
      _ = carstate.leftBlindspot
      _ = carstate.rightBlindspot
      return True
    except (AttributeError, Exception):
      # Si no hay atributos BSM o hay error, no hay BSM disponible
      return False

  def _get_blindspot(self, carstate, direction):
    """Obtiene el estado del blindspot de forma segura.

    Args:
      carstate: Estado del coche
      direction: LaneChangeDirection.left o LaneChangeDirection.right

    Returns:
      True si hay blindspot detectado, False si no hay o si BSM no está disponible
    """
    try:
      if direction == LaneChangeDirection.left:
        return getattr(carstate, 'leftBlindspot', False)
      elif direction == LaneChangeDirection.right:
        return getattr(carstate, 'rightBlindspot', False)
      return False
    except (AttributeError, Exception):
      return False

  def check_and_force_lane_change_param(self, carstate):
    if not self.param_s.get_bool("c_carril") or self.lane_change_state != LaneChangeState.off:
      return

    # Izquierda
    if self.param_s.get_bool("ForceLaneChangeLeft"):
      self.param_s.put_bool("ForceLaneChangeLeft", False)
      if self._get_blindspot(carstate, LaneChangeDirection.left):
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
      if self._get_blindspot(carstate, LaneChangeDirection.right):
        #cloudlog.warning("🔴 Cambio a derecha bloqueado por ángulo muerto")
        return
      self.lane_change_direction = LaneChangeDirection.right
      self.lane_change_state = LaneChangeState.laneChangeStarting
      self.lane_change_ll_prob = 1.0
      self.lane_change_wait_timer = 0
      #cloudlog.info("➡️ Cambio de carril forzado a la derecha")



  def auto_overtake(self, carstate, d_rel, v_rel, set_speed, lead_status):
    """Adelantamiento automático unificado que detecta BSM automáticamente.

    Si el coche tiene BSM disponible, lo usa para verificar ángulo muerto.
    Si no tiene BSM, funciona sin verificación de ángulo muerto.
    Todas las referencias a BSM están protegidas con try/except para evitar errores.
    """
    try:
      # Verificar si el coche tiene BSM disponible
      has_bsm = self._has_bsm(carstate)

      # Inicializar variables si no existen
      if not hasattr(self, "overtake_start_time"):
        self.overtake_start_time = 0
      if not hasattr(self, "speed_increased"):
        self.speed_increased = False

      params = Params()
      params.put_bool("overtakingActive", self.overtake_active)

      # Verificar si el estado anterior era "FINALIZADO" para mantenerlo
      estado_anterior = params.get("overtakeStatus", encoding="utf8")
      if estado_anterior == "FINALIZADO" and not self.overtake_active:
        # Mantener FINALIZADO hasta que se reinicie el proceso (nuevo lead o reactivación)
        # Solo cambiar a ESPERANDO si hay un lead detectado (se reinicia el proceso)
        if not lead_status:
          params.put("overtakeStatus", "FINALIZADO")
          return  # Salir temprano para mantener el estado FINALIZADO

      # Actualizar estado del adelantamiento para el indicador visual
      # Determinar el estado actual basado en el flujo de adelantamiento
      if not self.overtake_active:
        # No está activo: esperando condiciones
        params.put("overtakeStatus", "ESPERANDO")
      elif self.lane_change_direction == LaneChangeDirection.left:
        # Cambiando a carril izquierdo
        if self.lane_change_state == LaneChangeState.laneChangeStarting:
          params.put("overtakeStatus", "CAMBIANDO_IZQ")
        elif self.lane_change_state == LaneChangeState.laneChangeFinishing:
          params.put("overtakeStatus", "CAMBIANDO_IZQ")
        else:
          # Ya en carril izquierdo, verificando si aumentó velocidad
          if self.speed_increased:
            # Verificar si está esperando para volver
            elapsed = time.time() - self.overtake_start_time
            return_time = 10.0 if has_bsm else 15.0
            if elapsed >= return_time * 0.5:  # Más de la mitad del tiempo
              params.put("overtakeStatus", "ESPERANDO_RETORNO")
            else:
              params.put("overtakeStatus", "ADELANTANDO")
          else:
            params.put("overtakeStatus", "ADELANTANDO")
      elif self.lane_change_direction == LaneChangeDirection.right:
        # Volviendo al carril derecho
        if self.lane_change_state == LaneChangeState.laneChangeStarting:
          params.put("overtakeStatus", "VOLVIENDO")
        elif self.lane_change_state == LaneChangeState.laneChangeFinishing:
          params.put("overtakeStatus", "VOLVIENDO")
        else:
          params.put("overtakeStatus", "ADELANTANDO")
      else:
        # Estado por defecto cuando está activo
        params.put("overtakeStatus", "ADELANTANDO")

      # Actualizar parámetros de estado (protegido para BSM)
      try:
        right_blindspot = self._get_blindspot(carstate, LaneChangeDirection.right)
        params.put_bool("waitingToReturn", self.overtake_active and self.overtake_timer > 5.0 and not right_blindspot)
        params.put_bool("returningRight", self.overtake_timer > 10.0 and not right_blindspot)
      except Exception:
        # Si hay error accediendo a BSM, asumir que no hay blindspot
        params.put_bool("waitingToReturn", self.overtake_active and self.overtake_timer > 5.0)
        params.put_bool("returningRight", self.overtake_timer > 10.0)

      # --- INICIAR ADELANTAMIENTO ---
      if not self.overtake_active and lead_status:
        distancia_ok = d_rel < 50.0

        # Si tiene BSM, usar umbral más alto (36 km/h). Si no, usar umbral más bajo (15 km/h)
        if has_bsm:
          velocidad_ok = (carstate.cruiseSpeed - carstate.vEgo) > 10.0  # 36 km/h
          speed_delta = 10.0  # m/s ≈ +36 km/h
          return_time = 10.0  # segundos
        else:
          velocidad_ok = (set_speed - carstate.vEgo) > 4.166  # 15 km/h
          speed_delta = 4.166  # m/s ≈ +15 km/h
          return_time = 15.0  # segundos

        if distancia_ok and velocidad_ok:
          # Verificar blindspot izquierdo si hay BSM disponible
          try:
            left_blindspot = self._get_blindspot(carstate, LaneChangeDirection.left)
            if has_bsm and left_blindspot:
              # Hay blindspot, no iniciar adelantamiento
              params.put("overtakeStatus", "BLOQUEADO")
              return
          except Exception:
            # Si hay error, continuar sin verificación
            pass

          # Guardar velocidad inicial
          if has_bsm:
            self.overtake_v_cruise_last = carstate.cruiseSpeed
            params.put("OverrideCruiseSpeed", str(self.overtake_v_cruise_last + speed_delta))
          else:
            self.original_set_speed = set_speed
            self.params.put("vel_adel", str(self.original_set_speed * 3.6))  # Guardar en km/h

          # Iniciar adelantamiento → cambio a la izquierda
          self.lane_change_direction = LaneChangeDirection.left
          self.lane_change_state = LaneChangeState.laneChangeStarting
          self.lane_change_ll_prob = 1.0
          self.lane_change_wait_timer = 0
          self.overtake_active = True
          self.overtake_timer = 0.0
          self.overtake_start_time = time.time()
          self.speed_increased = False

          bsm_text = "con BSM" if has_bsm else "sin BSM"
          cloudlog.info(f"🟢 Adelantamiento automático ({bsm_text}) activado")

      # --- MIENTRAS ADELANTA ---
      elif self.overtake_active:
        self.overtake_timer += DT_MDL
        elapsed = time.time() - self.overtake_start_time

        # Aumentar velocidad solo una vez
        if not self.speed_increased:
          if has_bsm:
            # Ya se configuró en OverrideCruiseSpeed al iniciar
            self.speed_increased = True
          else:
            # Aumentar velocidad usando vel_adel
            new_speed = (self.original_set_speed * 3.6) + 15
            self.params.put("vel_adel", str(new_speed))
            self.v_cruise_helper.v_cruise_kph = new_speed
            self.speed_increased = True
            cloudlog.info(f"⬆️ Velocidad incrementada +15 km/h: {new_speed:.1f} km/h")

        # Determinar tiempo de retorno según si hay BSM
        return_time = 10.0 if has_bsm else 15.0

        # Verificar si es momento de volver al carril derecho
        if elapsed >= return_time:
          # Si tiene BSM, verificar blindspot derecho antes de volver
          can_return = True
          if has_bsm:
            try:
              right_blindspot = self._get_blindspot(carstate, LaneChangeDirection.right)
              can_return = not right_blindspot
            except Exception:
              # Si hay error, permitir retorno
              can_return = True

          if can_return:
            self.lane_change_direction = LaneChangeDirection.right
            self.lane_change_state = LaneChangeState.laneChangeStarting
            self.lane_change_ll_prob = 1.0
            self.lane_change_wait_timer = 0
            self.overtake_active = False

            # Restaurar velocidad original
            if has_bsm:
              if self.overtake_v_cruise_last is not None:
                params.put("OverrideCruiseSpeed", str(self.overtake_v_cruise_last))
            else:
              self.params.put("vel_adel", str(self.original_set_speed * 3.6))
              self.v_cruise_helper.v_cruise_kph = self.original_set_speed * 3.6

            params.put("overtakeStatus", "FINALIZADO")
            cloudlog.info("🔵 Adelantamiento completado: retorno al carril derecho")

    except Exception as e:
      cloudlog.error(f"❌ Error en lógica de adelantamiento: {e}")

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

    if self.param_s.get_bool("sic_adelantar"):
      # Adelantamiento automático unificado (detecta BSM automáticamente)
      self.auto_overtake(carstate, d_rel, v_rel, set_speed, lead_status)
    else:
      # Si el adelantamiento está desactivado, actualizar estado
      params = Params()
      params.put("overtakeStatus", "DESACTIVADO")

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

        # Verificar blindspot de forma segura (protegido para coches sin BSM)
        try:
          left_bsm = self._get_blindspot(carstate, LaneChangeDirection.left)
          right_bsm = self._get_blindspot(carstate, LaneChangeDirection.right)
          blindspot_detected = ((left_bsm and self.lane_change_direction == LaneChangeDirection.left) or
                                (right_bsm and self.lane_change_direction == LaneChangeDirection.right))
        except Exception:
          # Si hay error accediendo a BSM, asumir que no hay blindspot
          blindspot_detected = False

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
