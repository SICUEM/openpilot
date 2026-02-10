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
    self.last_d_rel = None  # Guardar distancia anterior para detectar transición

    self.CP = messaging.log_from_bytes(self.params.get("CarParams", block=True), car.CarParams)

      # Uses car interface helper functions, altering state won't be considered by card for actuation
    self.speed_increased = False
    
    # Parámetros configurables de adelantamiento (valores por defecto)
    self.overtake_distancia_activacion = 50.0  # metros
    self.overtake_tiempo_carril_izq = 15.0  # segundos
    self.overtake_incremento_velocidad = 15.0  # km/h

    self.v_cruise_helper = VCruiseHelper(self.CP)

    controls_state_bytes = self.params.get("ReplayControlsState")
    if controls_state_bytes:
      controls_state = log.ControlsState.from_bytes(controls_state_bytes)
      self.v_cruise_helper.v_cruise_kph = controls_state.vCruise
    else:
      # Si no existe, ponemos un valor seguro por defecto (ej. 30 km/h)
      self.v_cruise_helper.v_cruise_kph = 30

  def read_param(self):
    self.edge_toggle = self.param_s.get_bool("RoadEdge")
    self.lane_change_set_timer = int(self.param_s.get("AutoLaneChangeTimer", encoding="utf8"))
    self.lane_change_bsm_delay = self.param_s.get_bool("AutoLaneChangeBsmDelay")
    
    # Leer parámetros configurables de adelantamiento
    self._read_overtake_params()
  
  def _read_overtake_params(self):
    """Lee los parámetros configurables de adelantamiento desde Params.
    
    Valores configurables vía MQTT:
    - overtake_distancia_activacion: 20-100 metros (default 50)
    - overtake_tiempo_carril_izq: 5-30 segundos (default 15)
    - overtake_incremento_velocidad: 5-30 km/h (default 15)
    """
    try:
      # Distancia de activación (default 50m)
      distancia_raw = self.params.get("overtake_distancia_activacion")
      if distancia_raw:
        distancia = float(distancia_raw.decode("utf-8") if isinstance(distancia_raw, bytes) else distancia_raw)
        if 20.0 <= distancia <= 100.0:
          self.overtake_distancia_activacion = distancia
      
      # Tiempo en carril izquierdo (default 15s)
      tiempo_raw = self.params.get("overtake_tiempo_carril_izq")
      if tiempo_raw:
        tiempo = float(tiempo_raw.decode("utf-8") if isinstance(tiempo_raw, bytes) else tiempo_raw)
        if 5.0 <= tiempo <= 30.0:
          self.overtake_tiempo_carril_izq = tiempo
      
      # Incremento de velocidad (default 15 km/h)
      incremento_raw = self.params.get("overtake_incremento_velocidad")
      if incremento_raw:
        incremento = float(incremento_raw.decode("utf-8") if isinstance(incremento_raw, bytes) else incremento_raw)
        if 5.0 <= incremento <= 30.0:
          self.overtake_incremento_velocidad = incremento
    except Exception:
      pass  # Usar valores por defecto si hay error

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

    # Inicializar variables de espera BSM si no existen
    if not hasattr(self, "waiting_bsm_left"):
      self.waiting_bsm_left = False
    if not hasattr(self, "waiting_bsm_right"):
      self.waiting_bsm_right = False

    # Obtener estado del BSM
    left_bsm = self._get_blindspot(carstate, LaneChangeDirection.left)
    right_bsm = self._get_blindspot(carstate, LaneChangeDirection.right)

    # --- ESTADO: ESPERANDO BSM IZQUIERDO LIBRE ---
    if self.waiting_bsm_left:
      if not left_bsm:
        # BSM izquierdo libre → ejecutar cambio de carril
        self.waiting_bsm_left = False
        self.param_s.put("bsmLaneChangeStatus", "CARRIL_LIBRE_IZQ")
        self.lane_change_direction = LaneChangeDirection.left
        self.lane_change_state = LaneChangeState.laneChangeStarting
        self.lane_change_ll_prob = 1.0
        self.lane_change_wait_timer = 0
        if self.param_s.get_bool("modo_debug"):
          print("✅ BSM izquierdo libre - Cambiando de carril")
      else:
        # BSM sigue ocupado, seguir esperando
        self.param_s.put("bsmLaneChangeStatus", "CARRIL_OCUPADO_IZQ")
      return

    # --- ESTADO: ESPERANDO BSM DERECHO LIBRE ---
    if self.waiting_bsm_right:
      if not right_bsm:
        # BSM derecho libre → ejecutar cambio de carril
        self.waiting_bsm_right = False
        self.param_s.put("bsmLaneChangeStatus", "CARRIL_LIBRE_DER")
        self.lane_change_direction = LaneChangeDirection.right
        self.lane_change_state = LaneChangeState.laneChangeStarting
        self.lane_change_ll_prob = 1.0
        self.lane_change_wait_timer = 0
        if self.param_s.get_bool("modo_debug"):
          print("✅ BSM derecho libre - Cambiando de carril")
      else:
        # BSM sigue ocupado, seguir esperando
        self.param_s.put("bsmLaneChangeStatus", "CARRIL_OCUPADO_DER")
      return

    # Izquierda
    if self.param_s.get_bool("ForceLaneChangeLeft"):
      self.param_s.put_bool("ForceLaneChangeLeft", False)
      # Primero mostrar "REVISANDO_BSM"
      self.param_s.put("bsmLaneChangeStatus", "REVISANDO_BSM_IZQ")

      if left_bsm:
        # BSM ocupado → entrar en estado de espera
        self.waiting_bsm_left = True
        self.param_s.put("bsmLaneChangeStatus", "CARRIL_OCUPADO_IZQ")
        if self.param_s.get_bool("modo_debug"):
          print("⚠️ BSM izquierdo ocupado - Esperando para cambiar")
        return

      # BSM libre → cambiar de carril
      self.param_s.put("bsmLaneChangeStatus", "CARRIL_LIBRE_IZQ")
      self.lane_change_direction = LaneChangeDirection.left
      self.lane_change_state = LaneChangeState.laneChangeStarting
      self.lane_change_ll_prob = 1.0
      self.lane_change_wait_timer = 0
      return

    # Derecha
    if self.param_s.get_bool("ForceLaneChangeRight"):
      self.param_s.put_bool("ForceLaneChangeRight", False)
      # Primero mostrar "REVISANDO_BSM"
      self.param_s.put("bsmLaneChangeStatus", "REVISANDO_BSM_DER")

      if right_bsm:
        # BSM ocupado → entrar en estado de espera
        self.waiting_bsm_right = True
        self.param_s.put("bsmLaneChangeStatus", "CARRIL_OCUPADO_DER")
        if self.param_s.get_bool("modo_debug"):
          print("⚠️ BSM derecho ocupado - Esperando para cambiar")
        return

      # BSM libre → cambiar de carril
      self.param_s.put("bsmLaneChangeStatus", "CARRIL_LIBRE_DER")
      self.lane_change_direction = LaneChangeDirection.right
      self.lane_change_state = LaneChangeState.laneChangeStarting
      self.lane_change_ll_prob = 1.0
      self.lane_change_wait_timer = 0

    # Limpiar estado si no hay cambio de carril pendiente
    if not self.waiting_bsm_left and not self.waiting_bsm_right:
      # Solo limpiar si el estado no es uno activo
      estado_actual = self.param_s.get("bsmLaneChangeStatus", encoding="utf8")
      if estado_actual and estado_actual not in ("CARRIL_OCUPADO_IZQ", "CARRIL_OCUPADO_DER"):
        self.param_s.put("bsmLaneChangeStatus", "")



  def test_overtake_routine(self, carstate, set_speed):
    """Rutina de prueba de adelantamiento para simulador (sin depender de coches).

    Ejecuta automáticamente:
    1. Cambio a carril izquierdo
    2. Aumento de velocidad +15 km/h
    3. Espera 15 segundos
    4. Cambio a carril derecho
    5. Restauración de velocidad original
    """
    try:
      params = Params()

      # Inicializar variables si no existen
      if not hasattr(self, "test_overtake_start_time"):
        self.test_overtake_start_time = None
        self.test_overtake_original_speed = None
        self.test_overtake_state = "INICIO"  # INICIO, CAMBIANDO_IZQ, ADELANTANDO, CAMBIANDO_DER, FINALIZADO

      current_time = time.time()

      # Estado INICIO: Preparar y comenzar
      if self.test_overtake_state == "INICIO":
        # Leer parámetros configurables (valores dinámicos desde MQTT)
        self._read_overtake_params()
        
        # Guardar velocidad original REAL desde set_speed (que viene de controlsd)
        # set_speed está en m/s, convertir a km/h
        self.test_overtake_original_speed = set_speed * 3.6
        if self.test_overtake_original_speed is None or self.test_overtake_original_speed <= 0:
          # Fallback: usar velocidad del v_cruise_helper si set_speed no es válido
          self.test_overtake_original_speed = self.v_cruise_helper.v_cruise_kph if self.v_cruise_helper.v_cruise_kph > 0 else 30.0

        # 1) PRIMERO: Activar el adelantamiento y escribir el parámetro ANTES de aumentar velocidad
        # Esto evita que controlsd limpie el parámetro antes de usarlo
        params.put_bool("overtakingActive", True)

        # 2) SEGUNDO: Aumentar velocidad usando el mismo método que los botones de la app
        # Usar incremento configurable (default 15 km/h, configurable 5-30 km/h vía MQTT)
        incremento_vel = self.overtake_incremento_velocidad
        if self.test_overtake_original_speed is not None:
          new_speed = min(self.test_overtake_original_speed + incremento_vel, 145.0)
          try:
            params.put("OvertakeTargetSpeedKph", f"{new_speed:.1f}")
            # Log para modo debug con valores dinámicos
            if self.param_s.get_bool("modo_debug"):
              print(f"🧪 TEST ADELANTAMIENTO - +Vel: {incremento_vel}km/h, Tiempo: {self.overtake_tiempo_carril_izq}s")
          except Exception:
            pass  # Error silencioso para reducir uso de memoria

        # 3) TERCERO: Iniciar cambio a carril izquierdo
        self.lane_change_direction = LaneChangeDirection.left
        self.lane_change_state = LaneChangeState.laneChangeStarting
        self.lane_change_ll_prob = 1.0
        self.lane_change_wait_timer = 0
        self.test_overtake_start_time = current_time
        self.test_overtake_state = "ADELANTANDO"
        params.put("overtakeStatus", "ADELANTANDO")

      # Estado ADELANTANDO: esperar tiempo configurable antes de volver al carril derecho
      elif self.test_overtake_state == "ADELANTANDO":
        elapsed = current_time - self.test_overtake_start_time
        tiempo_carril_izq = self.overtake_tiempo_carril_izq  # Default 15s, configurable 5-30s
        if elapsed >= tiempo_carril_izq:
          # Tiempo cumplido, cambiar a carril derecho
          self.lane_change_direction = LaneChangeDirection.right
          self.lane_change_state = LaneChangeState.laneChangeStarting
          self.lane_change_ll_prob = 1.0
          self.lane_change_wait_timer = 0
          self.test_overtake_start_time = current_time  # Resetear para el cambio derecho
          self.test_overtake_state = "CAMBIANDO_DER"
          params.put("overtakeStatus", "VOLVIENDO")
          # Log eliminado para reducir uso de memoria

      # Estado CAMBIANDO_DER: Esperar a que termine el cambio de carril
      elif self.test_overtake_state == "CAMBIANDO_DER":
        # Verificar si el cambio de carril ha terminado
        if self.lane_change_state not in (LaneChangeState.laneChangeStarting, LaneChangeState.laneChangeFinishing):
          # Cambio completado, restaurar velocidad y finalizar
          if self.test_overtake_original_speed is not None:
            try:
              # Restaurar velocidad original usando OvertakeTargetSpeedKph
              params.put("OvertakeTargetSpeedKph", f"{self.test_overtake_original_speed:.1f}")
              # El parámetro se limpiará automáticamente en controlsd cuando overtakingActive sea False
            except Exception:
              pass  # Error silencioso para reducir uso de memoria

          # Desactivar el adelantamiento para que controlsd limpie OvertakeTargetSpeedKph
          params.put_bool("overtakingActive", False)
          self.test_overtake_state = "FINALIZADO"
          params.put("overtakeStatus", "FINALIZADO")

      # Estado FINALIZADO: Mantener estado hasta que se desactive el toggle
      elif self.test_overtake_state == "FINALIZADO":
        params.put("overtakeStatus", "FINALIZADO")
        # Si se desactiva el toggle, resetear para permitir nueva ejecución
        if not self.param_s.get_bool("test_overtake_simulador"):
          self.test_overtake_state = "INICIO"
          self.test_overtake_start_time = None
          self.test_overtake_original_speed = None

    except Exception:
      pass  # Error silencioso para reducir uso de memoria

  def auto_overtake(self, carstate, d_rel, v_rel, set_speed, lead_status):
    """Adelantamiento automático con verificación de BSM (Blind Spot Monitoring).

    Algoritmo:
    1. Detecta coche delante a menos de 50m (configurable)
    2. Verifica que no hay coche en el punto ciego izquierdo (BSM)
    3. Si BSM izquierdo está libre → Cambia de carril a la izquierda
    4. Si BSM izquierdo ocupado → Espera hasta que esté libre
    5. Aumenta velocidad en +15 km/h (configurable)
    6. Espera tiempo configurable (default 15s)
    7. Verifica que no hay coche en el punto ciego derecho (BSM)
    8. Si BSM derecho está libre → Vuelve al carril derecho
    9. Si BSM derecho ocupado → Espera hasta que esté libre
    10. Restaura velocidad original
    """
    try:
      # Inicializar variables si no existen
      if not hasattr(self, "overtake_start_time"):
        self.overtake_start_time = 0
      if not hasattr(self, "speed_increased"):
        self.speed_increased = False
      if not hasattr(self, "original_v_cruise_kph"):
        self.original_v_cruise_kph = None
      if not hasattr(self, "overtake_waiting_left_bsm"):
        self.overtake_waiting_left_bsm = False  # Esperando para cambiar a izquierda
      if not hasattr(self, "overtake_waiting_right_bsm"):
        self.overtake_waiting_right_bsm = False  # Esperando para volver a derecha

      params = Params()
      # NOTA: overtakingActive se escribe más abajo, justo cuando cambia de estado
      # para evitar race conditions con controlsd

      # Obtener estado del BSM
      left_bsm = self._get_blindspot(carstate, LaneChangeDirection.left)
      right_bsm = self._get_blindspot(carstate, LaneChangeDirection.right)

      # Verificar si el estado anterior era "FINALIZADO" para mantenerlo
      estado_anterior = params.get("overtakeStatus", encoding="utf8")
      if estado_anterior == "FINALIZADO" and not self.overtake_active and not self.overtake_waiting_left_bsm:
        # Mantener FINALIZADO hasta que se reinicie el proceso (nuevo lead o reactivación)
        if not lead_status:
          params.put("overtakeStatus", "FINALIZADO")
          return  # Salir temprano para mantener el estado FINALIZADO

      # Actualizar estado del adelantamiento para el indicador visual
      if self.overtake_waiting_left_bsm:
        # Esperando a que se libere el BSM izquierdo para poder cambiar
        params.put("overtakeStatus", "BSM_IZQ_OCUPADO")
      elif self.overtake_waiting_right_bsm:
        # Esperando a que se libere el BSM derecho para poder volver
        params.put("overtakeStatus", "BSM_DER_OCUPADO")
      elif not self.overtake_active:
        params.put("overtakeStatus", "ESPERANDO")
        params.put_bool("overtakingActive", False)
      elif self.lane_change_direction == LaneChangeDirection.left:
        # Cambiando a carril izquierdo o ya en carril izquierdo
        if self.lane_change_state in (LaneChangeState.laneChangeStarting, LaneChangeState.laneChangeFinishing):
          params.put("overtakeStatus", "CAMBIANDO_IZQ")
        else:
          # Ya en carril izquierdo, verificando si aumentó velocidad
          elapsed = time.time() - self.overtake_start_time
          return_time = self.overtake_tiempo_carril_izq  # Tiempo configurable vía MQTT
          if elapsed >= return_time * 0.5:  # Más de la mitad del tiempo
            params.put("overtakeStatus", "ESPERANDO_RETORNO")
          else:
            params.put("overtakeStatus", "ADELANTANDO")
      elif self.lane_change_direction == LaneChangeDirection.right:
        # Volviendo al carril derecho
        if self.lane_change_state in (LaneChangeState.laneChangeStarting, LaneChangeState.laneChangeFinishing):
          params.put("overtakeStatus", "VOLVIENDO")
        else:
          params.put("overtakeStatus", "ADELANTANDO")
      else:
        params.put("overtakeStatus", "ADELANTANDO")

      # --- ESTADO: ESPERANDO PARA CAMBIAR A IZQUIERDA (BSM bloqueado) ---
      if self.overtake_waiting_left_bsm:
        if not left_bsm:
          # BSM izquierdo libre → ahora sí podemos cambiar y aumentar velocidad
          self.overtake_waiting_left_bsm = False

          # AHORA sí aumentamos velocidad (solo cuando BSM está libre)
          incremento_vel = self.overtake_incremento_velocidad
          if self.original_v_cruise_kph is not None:
            new_speed = min(self.original_v_cruise_kph + incremento_vel, 145.0)
            try:
              params.put("OvertakeTargetSpeedKph", f"{new_speed:.1f}")
              self.speed_increased = True
            except Exception:
              pass

          # Iniciar cambio a la izquierda
          self.lane_change_direction = LaneChangeDirection.left
          self.lane_change_state = LaneChangeState.laneChangeStarting
          self.lane_change_ll_prob = 1.0
          self.lane_change_wait_timer = 0
          self.overtake_timer = 0.0
          self.overtake_start_time = time.time()

          if self.param_s.get_bool("modo_debug"):
            print("✅ BSM izquierdo libre - Iniciando cambio de carril y aumentando velocidad")
        else:
          # BSM sigue ocupado, seguir esperando (sin aumentar velocidad)
          if self.param_s.get_bool("modo_debug"):
            print("⏳ Esperando BSM izquierdo libre...")
        return  # Salir para seguir verificando en la próxima iteración

      # --- ESTADO: ESPERANDO PARA VOLVER A DERECHA (BSM bloqueado) ---
      if self.overtake_waiting_right_bsm:
        if not right_bsm:
          # BSM derecho libre → ahora sí podemos volver y restaurar velocidad
          self.overtake_waiting_right_bsm = False

          # Cambiar de carril a la derecha
          self.lane_change_direction = LaneChangeDirection.right
          self.lane_change_state = LaneChangeState.laneChangeStarting
          self.lane_change_ll_prob = 1.0
          self.lane_change_wait_timer = 0

          # AHORA sí restauramos velocidad (solo cuando BSM está libre y vamos a cambiar)
          if self.original_v_cruise_kph is not None:
            try:
              params.put("OvertakeTargetSpeedKph", f"{self.original_v_cruise_kph:.1f}")
            except Exception:
              pass

          # Desactivar el adelantamiento
          self.overtake_active = False
          params.put_bool("overtakingActive", False)
          self.speed_increased = False

          params.put("overtakeStatus", "VOLVIENDO")
          # Limpiar para el próximo adelantamiento
          self.original_v_cruise_kph = None
          self.last_d_rel = None

          if self.param_s.get_bool("modo_debug"):
            print("✅ BSM derecho libre - Volviendo al carril derecho y restaurando velocidad")
        else:
          # BSM sigue ocupado, mantener velocidad aumentada y seguir esperando
          if self.param_s.get_bool("modo_debug"):
            print("⏳ Esperando BSM derecho libre (manteniendo velocidad)...")
        return  # Salir para seguir verificando en la próxima iteración

      # --- INICIAR ADELANTAMIENTO ---
      if not self.overtake_active and lead_status:
        # Leer parámetros configurables (valores dinámicos desde MQTT)
        self._read_overtake_params()
        dist_activacion = self.overtake_distancia_activacion  # Default 50m, configurable 20-100m

        # Condición: solo iniciar si pasamos de >distancia a <distancia (transición)
        # Si ya estábamos <distancia desde el principio, NO iniciar

        # Inicializar last_d_rel si es la primera vez
        if self.last_d_rel is None:
          self.last_d_rel = d_rel

        # Verificar transición: distancia anterior >dist_activacion y actual <dist_activacion
        distancia_anterior_ok = self.last_d_rel > dist_activacion
        distancia_actual_ok = d_rel < dist_activacion

        if distancia_anterior_ok and distancia_actual_ok:
          # Guardar velocidad original REAL desde set_speed (que viene de controlsd)
          # set_speed está en m/s, convertir a km/h
          self.original_v_cruise_kph = set_speed * 3.6
          if self.original_v_cruise_kph is None or self.original_v_cruise_kph <= 0:
            # Fallback: usar velocidad del v_cruise_helper si set_speed no es válido
            self.original_v_cruise_kph = self.v_cruise_helper.v_cruise_kph if self.v_cruise_helper.v_cruise_kph > 0 else 30.0

          # Verificar BSM izquierdo ANTES de hacer cualquier cosa
          if left_bsm:
            # BSM izquierdo ocupado → esperar hasta que esté libre
            # NO aumentamos velocidad, NO activamos adelantamiento aún
            self.overtake_waiting_left_bsm = True
            self.overtake_active = True  # Marcar como activo para que siga en el bucle
            params.put_bool("overtakingActive", True)
            params.put("overtakeStatus", "BSM_IZQ_OCUPADO")
            if self.param_s.get_bool("modo_debug"):
              print(f"⚠️ BSM izquierdo ocupado - Esperando para adelantar (Dist: {dist_activacion}m)")
          else:
            # BSM libre → activar adelantamiento, aumentar velocidad y cambiar de carril
            self.overtake_active = True
            params.put_bool("overtakingActive", True)

            # Aumentar velocidad (solo si BSM está libre)
            incremento_vel = self.overtake_incremento_velocidad
            if self.original_v_cruise_kph is not None:
              new_speed = min(self.original_v_cruise_kph + incremento_vel, 145.0)  # Máximo 145 km/h
              try:
                params.put("OvertakeTargetSpeedKph", f"{new_speed:.1f}")
                self.speed_increased = True
                if self.param_s.get_bool("modo_debug"):
                  print(f"🚗 ADELANTAMIENTO INICIADO - Dist: {dist_activacion}m, +Vel: {incremento_vel}km/h, Tiempo: {self.overtake_tiempo_carril_izq}s")
              except Exception:
                pass

            # Iniciar cambio a la izquierda inmediatamente
            self.lane_change_direction = LaneChangeDirection.left
            self.lane_change_state = LaneChangeState.laneChangeStarting
            self.lane_change_ll_prob = 1.0
            self.lane_change_wait_timer = 0
            self.overtake_timer = 0.0
            self.overtake_start_time = time.time()

        # Actualizar distancia anterior para la próxima iteración
        self.last_d_rel = d_rel

      # --- MIENTRAS ADELANTA ---
      elif self.overtake_active:
        self.overtake_timer += DT_MDL
        elapsed = time.time() - self.overtake_start_time

        # Tiempo de retorno configurable (default 15s, configurable 5-30s vía MQTT)
        return_time = self.overtake_tiempo_carril_izq

        # Verificar si es momento de volver al carril derecho
        if elapsed >= return_time:
          # Verificar BSM derecho ANTES de hacer cualquier cosa
          if right_bsm:
            # BSM derecho ocupado → esperar hasta que esté libre
            # NO bajamos velocidad, mantenemos velocidad aumentada mientras esperamos
            self.overtake_waiting_right_bsm = True
            params.put("overtakeStatus", "BSM_DER_OCUPADO")
            if self.param_s.get_bool("modo_debug"):
              print("⚠️ BSM derecho ocupado - Esperando para volver (manteniendo velocidad)")
          else:
            # BSM libre → restaurar velocidad y cambiar de carril a la derecha
            # PRIMERO: Restaurar velocidad original
            if self.original_v_cruise_kph is not None:
              try:
                params.put("OvertakeTargetSpeedKph", f"{self.original_v_cruise_kph:.1f}")
              except Exception:
                pass

            # Cambiar de carril a la derecha
            self.lane_change_direction = LaneChangeDirection.right
            self.lane_change_state = LaneChangeState.laneChangeStarting
            self.lane_change_ll_prob = 1.0
            self.lane_change_wait_timer = 0

            # Desactivar el adelantamiento
            self.overtake_active = False
            params.put_bool("overtakingActive", False)
            self.speed_increased = False

            params.put("overtakeStatus", "FINALIZADO")
            # Limpiar para el próximo adelantamiento
            self.original_v_cruise_kph = None
            self.last_d_rel = None

    except Exception:
      pass  # Error silencioso para reducir uso de memoria

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

    # Obtener datos de carControl
    try:
      if self.sm.updated['carControl']:
        car_control = self.sm['carControl']
        set_speed = car_control.hudControl.setSpeed
      else:
        set_speed = 0.1
    except Exception as e:
      set_speed = 0.1

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

    # Verificar si está activado el modo de prueba para simulador
    test_overtake_mode = self.param_s.get_bool("test_overtake_simulador")

    if test_overtake_mode:
      # Modo de prueba para simulador: ejecutar rutina sin depender de coches
      self.test_overtake_routine(carstate, set_speed)
    elif self.param_s.get_bool("sic_adelantar"):
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
      # Limpiar estado de BSM cuando el cambio de carril termina o se cancela
      if hasattr(self, 'waiting_bsm_left'):
        self.waiting_bsm_left = False
      if hasattr(self, 'waiting_bsm_right'):
        self.waiting_bsm_right = False
      self.param_s.put("bsmLaneChangeStatus", "")
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
        # 1. Establecer direccion
        self.lane_change_direction = LaneChangeDirection.left if \
          carstate.leftBlinker else LaneChangeDirection.right

        # 2. Chequear BSM INMEDIATAMENTE (antes de timer/torque)
        left_bsm = self._get_blindspot(carstate, LaneChangeDirection.left)
        right_bsm = self._get_blindspot(carstate, LaneChangeDirection.right)
        blindspot_detected = ((left_bsm and self.lane_change_direction == LaneChangeDirection.left) or
                              (right_bsm and self.lane_change_direction == LaneChangeDirection.right))

        # 3. Calcular condiciones de torque y timer
        torque_applied = carstate.steeringPressed and \
                         ((carstate.steeringTorque > 0 and self.lane_change_direction == LaneChangeDirection.left) or
                          (carstate.steeringTorque < 0 and self.lane_change_direction == LaneChangeDirection.right))

        self.lane_change_wait_timer += DT_MDL
        auto_lane_change_allowed = lane_change_auto_timer and self.lane_change_wait_timer > lane_change_auto_timer

        if carstate.brakePressed and not self.prev_brake_pressed:
          self.prev_brake_pressed = carstate.brakePressed

        # 4. Evaluar condiciones (BSM PRIMERO)
        if not one_blinker or below_lane_change_speed:
          # Intermitente soltado o velocidad baja -> cancelar
          self.lane_change_state = LaneChangeState.off
          self.lane_change_direction = LaneChangeDirection.none
          self.prev_lane_change = False
          self.prev_brake_pressed = False
          self.param_s.put("bsmLaneChangeStatus", "")

        elif blindspot_detected:
          # BSM OCUPADO -> BLOQUEAR cambio de carril
          if self.lane_change_direction == LaneChangeDirection.left:
            self.param_s.put("bsmLaneChangeStatus", "CARRIL_OCUPADO_IZQ")
          else:
            self.param_s.put("bsmLaneChangeStatus", "CARRIL_OCUPADO_DER")
          # Resetear timer para que haya pequeno delay cuando BSM se libere
          if lane_change_auto_timer:
            self.lane_change_wait_timer = min(self.lane_change_wait_timer, max(0, lane_change_auto_timer - 0.3))

        elif (torque_applied or (auto_lane_change_allowed and not self.prev_lane_change and not self.prev_brake_pressed)):
          # BSM LIBRE + condiciones cumplidas -> ejecutar cambio de carril
          if self.lane_change_direction == LaneChangeDirection.left:
            self.param_s.put("bsmLaneChangeStatus", "CARRIL_LIBRE_IZQ")
          else:
            self.param_s.put("bsmLaneChangeStatus", "CARRIL_LIBRE_DER")
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
          # Limpiar estado de BSM cuando el cambio de carril se completa
          self.param_s.put("bsmLaneChangeStatus", "")
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
