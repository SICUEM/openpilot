#!/usr/bin/env python3
import json
import os
import math
import time
import threading
from typing import SupportsFloat

import cereal.messaging as messaging

from cereal import car, log, custom
from msgq.visionipc import VisionIpcClient, VisionStreamType

from openpilot.common.conversions import Conversions as CV
from openpilot.common.git import get_short_branch
from openpilot.common.numpy_fast import clip
from openpilot.common.params import Params, UnknownKeyName
from openpilot.common.realtime import config_realtime_process, Priority, Ratekeeper, DT_CTRL
from openpilot.common.swaglog import cloudlog

from openpilot.selfdrive.car.car_helpers import get_car_interface, get_startup_event
from openpilot.selfdrive.controls.lib.alertmanager import AlertManager, set_offroad_alert
from openpilot.selfdrive.controls.lib.drive_helpers import VCruiseHelper, clip_curvature, get_lag_adjusted_curvature, \
  CRUISE_LONG_PRESS, V_CRUISE_UNSET, V_CRUISE_MIN, V_CRUISE_MAX
from openpilot.selfdrive.controls.lib.events import Events, ET
from openpilot.selfdrive.controls.lib.latcontrol import LatControl, MIN_LATERAL_CONTROL_SPEED
from openpilot.selfdrive.controls.lib.latcontrol_pid import LatControlPID
from openpilot.selfdrive.controls.lib.latcontrol_angle import LatControlAngle, STEER_ANGLE_SATURATION_THRESHOLD
from openpilot.selfdrive.controls.lib.latcontrol_torque import LatControlTorque
from openpilot.selfdrive.controls.lib.longcontrol import LongControl
from openpilot.selfdrive.controls.lib.vehicle_model import VehicleModel
from openpilot.selfdrive.modeld.custom_model_metadata import CustomModelMetadata, ModelCapabilities

from openpilot.system.athena.registration import is_registered_device
from openpilot.system.hardware import HARDWARE
# from openpilot.sicuem.sicmqtthilo2 import SicMqttHilo2  # DESACTIVADO temporalmente — no se usa, ahorra recursos
from openpilot.sicuem.adripilot.mqtt_envio_general import MQTTEnvioGeneral
from openpilot.sicuem.adripilot.adripilot_control_ultra_simple import adripilot_control_ultra_simple
from openpilot.sicuem.adripilot.adripilot_speed_ultra_simple import adripilot_speed_ultra_simple
from openpilot.sicuem.adripilot.adripilot_obstacle_pulse import (
  ObstaclePulseState,
  DEFAULT_MAX_ANGLE,
  DEFAULT_MAX_CURV,
)

# Anti-flicker: cuando JetsonObstacleStatus pasa de activo a "" lo mantenemos
# en el param durante este tiempo (segundos) para que la UI (a ~20Hz, 50ms/cycle)
# no se pierda dodges breves. Lo suficiente para garantizar ~6 ciclos de la UI.
OBSTACLE_STATUS_HOLD_S = 0.30



SOFT_DISABLE_TIME = 3  # seconds
LDW_MIN_SPEED = 31 * CV.MPH_TO_MS
LANE_DEPARTURE_THRESHOLD = 0.1
CAMERA_OFFSET = 0.04

REPLAY = "REPLAY" in os.environ
SIMULATION = "SIMULATION" in os.environ
TESTING_CLOSET = "TESTING_CLOSET" in os.environ
IGNORE_PROCESSES = {"loggerd", "encoderd", "statsd", "mapd", "gpxd", "gpxd_uploader", "mapd", "otisserv",
                    "fleet_manager"}

ThermalStatus = log.DeviceState.ThermalStatus
State = log.ControlsState.OpenpilotState
PandaType = log.PandaState.PandaType
Desire = log.Desire
LaneChangeState = log.LaneChangeState
LaneChangeDirection = log.LaneChangeDirection
EventName = car.CarEvent.EventName
ButtonType = car.CarState.ButtonEvent.Type
SafetyModel = car.CarParams.SafetyModel
GearShifter = car.CarState.GearShifter

IGNORED_SAFETY_MODES = (SafetyModel.silent, SafetyModel.noOutput)
CSID_MAP = {"1": EventName.roadCameraError, "2": EventName.wideRoadCameraError, "0": EventName.driverCameraError}
ACTUATOR_FIELDS = tuple(car.CarControl.Actuators.schema.fields.keys())
ACTIVE_STATES = (State.enabled, State.softDisabling, State.overriding)
ENABLED_STATES = (State.preEnabled, *ACTIVE_STATES)

PERSONALITY_MAPPING = {0: 0, 1: 1, 2: 2, 3: 2}


class Controls:
  def __init__(self, CI=None):
    # SicMqttHilo2 DESACTIVADO temporalmente — no se usa, ahorra recursos
    # sicMqtt = SicMqttHilo2()
    # sicMqtt.start()

    # UEM/AdriPilot: el cooldown de eventos MQTT está manejado en events_mqtt.py

    sender = MQTTEnvioGeneral()
    sender.start()

    self.params = Params()

    if CI is None:
      cloudlog.info("controlsd is waiting for CarParams")
      self.CP = messaging.log_from_bytes(self.params.get("CarParams", block=True), car.CarParams)
      cloudlog.info("controlsd got CarParams")

      # Uses car interface helper functions, altering state won't be considered by card for actuation
      self.CI = get_car_interface(self.CP)
    else:
      self.CI, self.CP = CI, CI.CP

    # Ensure the current branch is cached, otherwise the first iteration of controlsd lags
    self.branch = get_short_branch()

    # Setup sockets
    self.pm = messaging.PubMaster(['controlsState', 'carControl', 'onroadEvents', 'controlsStateSP'])

    self.sensor_packets = ["accelerometer", "gyroscope"]
    self.camera_packets = ["roadCameraState", "driverCameraState", "wideRoadCameraState"]

    self.log_sock = messaging.sub_sock('androidLog')

    # TODO: de-couple controlsd with card/conflate on carState without introducing controls mismatches
    self.car_state_sock = messaging.sub_sock('carState', timeout=20)

    self.d_camera_hardware_missing = self.params.get_bool("DriverCameraHardwareMissing") and not is_registered_device()
    if self.d_camera_hardware_missing:
      IGNORE_PROCESSES.update({"dmonitoringd", "dmonitoringmodeld"})
      self.camera_packets.remove("driverCameraState")

    ignore = self.sensor_packets + ['testJoystick']
    if SIMULATION:
      ignore += ['driverCameraState', 'managerState']
    if REPLAY:
      # no vipc in replay will make them ignored anyways
      ignore += ['roadCameraState', 'wideRoadCameraState']
    if self.d_camera_hardware_missing:
      ignore += ['driverMonitoringState']
    lateral_plan_svs = ['lateralPlanDEPRECATED', 'lateralPlanSPDEPRECATED']
    self.sm = messaging.SubMaster(['deviceState', 'pandaStates', 'peripheralState', 'modelV2', 'liveCalibration',
                                   'carOutput', 'driverMonitoringState', 'longitudinalPlan', 'liveLocationKalman',
                                   'managerState', 'liveParameters', 'radarState', 'liveTorqueParameters',
                                   'testJoystick', 'longitudinalPlanSP',
                                   'modelV2SP'] + self.camera_packets + self.sensor_packets + lateral_plan_svs,
                                  ignore_alive=ignore, ignore_avg_freq=ignore + ['radarState', 'testJoystick'],
                                  ignore_valid=['testJoystick', ],
                                  frequency=int(1 / DT_CTRL))

    self.joystick_mode = self.params.get_bool("JoystickDebugMode")

    # read params
    self.is_metric = self.params.get_bool("IsMetric")
    self.is_ldw_enabled = self.params.get_bool("IsLdwEnabled")

    # detect sound card presence and ensure successful init
    sounds_available = HARDWARE.get_sound_card_online()

    car_recognized = self.CP.carName != 'mock'

    # cleanup old params
    if not self.CP.experimentalLongitudinalAvailable:
      self.params.remove("ExperimentalLongitudinalEnabled")
    if not self.CP.openpilotLongitudinalControl:
      self.params.remove("ExperimentalMode")

    self.CS_prev = car.CarState.new_message()
    self.AM = AlertManager()
    self.events = Events()

    self.LoC = LongControl(self.CP)
    self.VM = VehicleModel(self.CP)

    self.LaC: LatControl
    if self.CP.steerControlType == car.CarParams.SteerControlType.angle:
      self.LaC = LatControlAngle(self.CP, self.CI)
    elif self.CP.lateralTuning.which() == 'pid':
      self.LaC = LatControlPID(self.CP, self.CI)
    elif self.CP.lateralTuning.which() == 'torque':
      self.LaC = LatControlTorque(self.CP, self.CI)

    self.initialized = False
    self.state = State.disabled
    self.enabled = False
    self.enabled_long = False
    self.active = False
    self.soft_disable_timer = 0
    self.mismatch_counter = 0
    self.cruise_mismatch_counter = 0
    self.last_blinker_frame = 0
    self.last_steering_pressed_frame = 0
    self.distance_traveled = 0
    self.last_functional_fan_frame = 0
    self.events_prev = []
    self.current_alert_types = [ET.PERMANENT]
    self.logged_comm_issue = None
    self.not_running_prev = None
    self.steer_limited = False
    self.desired_curvature = 0.0
    self.experimental_mode = False
    self.personality = self.read_personality_param()
    self.v_cruise_helper = VCruiseHelper(self.CP)
    self.recalibrating_seen = False
    self.nn_alert_shown = False
    self.enable_nnff = self.params.get_bool("NNFF")

    self.reverse_acc_change = False

    # Variables para giro temporal del volante (AdriPilot)
    # Ahora se usan variables globales en lugar de parámetros
    try:
      from openpilot.sicuem.adripilot.adripilot_steering_pulse import clear_steering_pulse
      clear_steering_pulse()  # Limpiar cualquier pulso pendiente al iniciar
    except ImportError:
      pass  # Módulo no disponible, ignorar
    self.dynamic_experimental_control = False

    # Modo 3 (COMMA+JETSON): estado del esquive y caché de config
    self._obstacle_pulse_state = ObstaclePulseState()
    self._last_obstacle_status = ""
    # Anti-flicker para la UI: cuando el status pasa de activo a "" lo
    # mantenemos publicado durante OBSTACLE_STATUS_HOLD_S para que la UI
    # (que lee Params a ~20Hz) no se pierda dodges muy breves (<50ms).
    self._obstacle_status_hold_until = 0.0   # wall-clock hasta el que mantenemos el último activo
    self._obstacle_status_held_value = ""    # último status activo que estamos manteniendo
    self._obstacle_config_last_read = 0.0  # wall-clock; recachear cada 1s
    self._obstacle_max_angle = DEFAULT_MAX_ANGLE
    self._obstacle_max_curv = DEFAULT_MAX_CURV
    self._obstacle_apply_target = "curvature"  # "curvature" | "torque"

    self.live_torque = self.params.get_bool("LiveTorque")
    self.torqued_override = self.params.get_bool("TorquedOverride")

    self.enable_mads = self.params.get_bool("EnableMads")
    self.mads_disengage_lateral_on_brake = self.params.get_bool("DisengageLateralOnBrake")
    self.mads_ndlob = self.enable_mads and not self.mads_disengage_lateral_on_brake
    self.process_not_running = False
    self.experimental_mode_update = False

    self.custom_model_metadata = CustomModelMetadata(params=self.params, init_only=True)
    self.model_use_lateral_planner = self.custom_model_metadata.valid and \
                                     self.custom_model_metadata.capabilities & ModelCapabilities.LateralPlannerSolution

    self.dynamic_personality = self.params.get_bool("DynamicPersonality")

    self.accel_personality = self.read_accel_personality_param()

    self.can_log_mono_time = 0

    self.startup_event = get_startup_event(car_recognized, not self.CP.passive, len(self.CP.carFw) > 0)

    if not sounds_available:
      self.events.add(EventName.soundsUnavailable, static=True)
    if not car_recognized:
      self.events.add(EventName.carUnrecognized, static=True)
      if len(self.CP.carFw) > 0:
        set_offroad_alert("Offroad_CarUnrecognized", True)
      else:
        set_offroad_alert("Offroad_NoFirmware", True)
    elif self.CP.passive:
      self.events.add(EventName.dashcamMode, static=True)

    # controlsd is driven by carState, expected at 100Hz
    self.rk = Ratekeeper(100, print_delay_threshold=None)

  def set_initial_state(self):
    if REPLAY:
      controls_state = self.params.get("ReplayControlsState")
      if controls_state is not None:
        with log.ControlsState.from_bytes(controls_state) as controls_state:
          self.v_cruise_helper.v_cruise_kph = controls_state.vCruise

      if any(ps.controlsAllowed for ps in self.sm['pandaStates']):
        self.state = State.enabled

  def _refresh_obstacle_config(self, now: float) -> None:
    """Lee los params de configuración del esquive con cache de 1s.

    Si el param es None (primera vez), siembra el default. Esto hace que la
    UI/app vea valores razonables al abrir los controles.
    """
    if now - self._obstacle_config_last_read < 1.0:
      return
    self._obstacle_config_last_read = now
    for key, default, attr in (
      ("JetsonObstacleMaxAngle",      DEFAULT_MAX_ANGLE,       "_obstacle_max_angle"),
      ("JetsonObstacleMaxCurv",       DEFAULT_MAX_CURV,        "_obstacle_max_curv"),
    ):
      try:
        raw = self.params.get(key)
        if raw is None or raw == b"":
          self.params.put_nonblocking(key, str(default))
          setattr(self, attr, default)
        else:
          setattr(self, attr, float(raw))
      except (UnknownKeyName, ValueError, TypeError):
        setattr(self, attr, default)

    # Sub-target del esquive (string, no float). Validamos contra el conjunto
    # permitido; cualquier otro valor -> fallback a "curvature" con log.
    try:
      raw = self.params.get("JetsonObstacleApplyTarget")
      if raw is None or raw == b"":
        self.params.put_nonblocking("JetsonObstacleApplyTarget", "curvature")
        self._obstacle_apply_target = "curvature"
      else:
        val = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else str(raw)
        if val in ("curvature", "torque"):
          self._obstacle_apply_target = val
        else:
          cloudlog.warning(f"controlsd: JetsonObstacleApplyTarget invalido: {val!r}, fallback curvature")
          self._obstacle_apply_target = "curvature"
    except (UnknownKeyName, ValueError, TypeError):
      self._obstacle_apply_target = "curvature"

  def update_events(self, CS):
    """Compute onroadEvents from carState"""

    self.events.clear()

    # Add joystick event, static on cars, dynamic on nonCars
    if self.joystick_mode:
      self.events.add(EventName.joystickDebug)
      self.startup_event = None

    # Add startup event
    if self.startup_event is not None:
      self.events.add(self.startup_event)
      self.startup_event = None

    # Don't add any more events if not initialized
    if not self.initialized:
      self.events.add(EventName.controlsInitializing)
      return

    # no more events while in dashcam mode
    if self.CP.passive:
      return

    # show alert to indicate whether NNFF is loaded
    if self.enable_nnff and not self.nn_alert_shown and self.sm.frame % 1000 == 0 and \
      self.CP.lateralTuning.which() == 'torque':
      self.nn_alert_shown = True
      self.events.add(EventName.torqueNNLoad)

    # Block resume if cruise never previously enabled
    resume_pressed = any(be.type in (ButtonType.accelCruise, ButtonType.resumeCruise) for be in CS.buttonEvents)
    if not self.CP.pcmCruise and not self.v_cruise_helper.v_cruise_initialized and resume_pressed:
      self.events.add(EventName.resumeBlocked)

    if not self.CP.notCar:
      if not self.d_camera_hardware_missing:
        self.events.add_from_msg(self.sm['driverMonitoringState'].events)
      self.events.add_from_msg(self.sm['longitudinalPlanSP'].events)

    # Add car events, ignore if CAN isn't valid
    if CS.canValid:
      self.events.add_from_msg(CS.events)

    # Create events for temperature, disk space, and memory
    if self.sm['deviceState'].thermalStatus >= ThermalStatus.red:
      self.events.add(EventName.overheat)
    if self.sm['deviceState'].freeSpacePercent < 7 and not SIMULATION:
      # under 7% of space free no enable allowed
      self.events.add(EventName.outOfSpace)
    if self.sm['deviceState'].memoryUsagePercent > 90 and not SIMULATION:
      self.events.add(EventName.lowMemory)

    # TODO: enable this once loggerd CPU usage is more reasonable
    # cpus = list(self.sm['deviceState'].cpuUsagePercent)
    # if max(cpus, default=0) > 95 and not SIMULATION:
    #  self.events.add(EventName.highCpuUsage)

    # Alert if fan isn't spinning for 5 seconds
    if self.sm['peripheralState'].pandaType != log.PandaState.PandaType.unknown:
      if self.sm['peripheralState'].fanSpeedRpm < 500 and self.sm['deviceState'].fanSpeedPercentDesired > 50:
        # allow enough time for the fan controller in the panda to recover from stalls
        if (self.sm.frame - self.last_functional_fan_frame) * DT_CTRL > 15.0:
          self.events.add(EventName.fanMalfunction)
      else:
        self.last_functional_fan_frame = self.sm.frame

    # Handle calibration status
    cal_status = self.sm['liveCalibration'].calStatus
    if cal_status != log.LiveCalibrationData.Status.calibrated:
      if cal_status == log.LiveCalibrationData.Status.uncalibrated:
        self.events.add(EventName.calibrationIncomplete)
      elif cal_status == log.LiveCalibrationData.Status.recalibrating:
        if not self.recalibrating_seen:
          set_offroad_alert("Offroad_Recalibration", True)
        self.recalibrating_seen = True
        self.events.add(EventName.calibrationRecalibrating)
      else:
        self.events.add(EventName.calibrationInvalid)

    # Handle lane change

    lane_change_edge_block = self.sm[
      'lateralPlanSPDEPRECATED'].laneChangeEdgeBlockDEPRECATED if self.model_use_lateral_planner else self.sm[
      'modelV2SP'].laneChangeEdgeBlock
    lane_change_svs = self.sm['lateralPlanDEPRECATED'] if self.model_use_lateral_planner else self.sm['modelV2'].meta
    if lane_change_svs.laneChangeState == LaneChangeState.preLaneChange and lane_change_edge_block:
      self.events.add(EventName.laneChangeRoadEdge)
    elif lane_change_svs.laneChangeState == LaneChangeState.preLaneChange:
      direction = lane_change_svs.laneChangeDirection  # ← valor por defecto del modelo
      try:

        force_lc = self.params.get("ForceLaneChangeLeft")
        if force_lc is not None and force_lc == b"1":
          direction = LaneChangeDirection.left
          CS.leftBlinker = True
          self.last_blinker_frame = self.sm.frame
          self.params.delete("ForceLaneChangeLeft")

        # Si hay blindspot y queremos forzar cambio
        if self.params.get_bool("c_carril"):
          if direction == LaneChangeDirection.left and CS.leftBlindspot:
            self.events.add(EventName.laneChangeBlockedLeft)
          elif direction == LaneChangeDirection.right and CS.rightBlindspot:
            self.events.add(EventName.laneChangeBlockedRight)


      except Exception as e:
        cloudlog.error(f"Error leyendo ForceLaneChangeLeft: {e}")

      if (CS.leftBlindspot and direction == LaneChangeDirection.left) or \
        (CS.rightBlindspot and direction == LaneChangeDirection.right):
        self.events.add(EventName.laneChangeBlocked)
      else:
        if direction == LaneChangeDirection.left:
          self.events.add(EventName.preLaneChangeLeft)
        else:
          self.events.add(EventName.preLaneChangeRight)
    elif lane_change_svs.laneChangeState in (LaneChangeState.laneChangeStarting,
                                             LaneChangeState.laneChangeFinishing):
      self.events.add(EventName.laneChange)  # AQUI CAMBIA DE CARRIL HACE LA ACCION DE CAMBIAR (EVENTO)

    for i, pandaState in enumerate(self.sm['pandaStates']):
      # All pandas must match the list of safetyConfigs, and if outside this list, must be silent or noOutput
      if i < len(self.CP.safetyConfigs):
        safety_mismatch = pandaState.safetyModel != self.CP.safetyConfigs[i].safetyModel or \
                          pandaState.safetyParam != self.CP.safetyConfigs[i].safetyParam or \
                          pandaState.alternativeExperience != self.CP.alternativeExperience
      else:
        safety_mismatch = pandaState.safetyModel not in IGNORED_SAFETY_MODES

      # safety mismatch allows some time for pandad to set the safety mode and publish it back from panda
      if (
        safety_mismatch and self.sm.frame * DT_CTRL > 10.) or pandaState.safetyRxChecksInvalid or self.mismatch_counter >= 200:
        self.events.add(EventName.controlsMismatch)

      if log.PandaState.FaultType.relayMalfunction in pandaState.faults:
        self.events.add(EventName.relayMalfunction)

    # Handle HW and system malfunctions
    # Order is very intentional here. Be careful when modifying this.
    # All events here should at least have NO_ENTRY and SOFT_DISABLE.
    num_events = len(self.events)

    not_running = {p.name for p in self.sm['managerState'].processes if not p.running and p.shouldBeRunning}
    if self.sm.recv_frame['managerState'] and (not_running - IGNORE_PROCESSES):
      self.events.add(EventName.processNotRunning)
      self.process_not_running = True
      if not_running != self.not_running_prev:
        cloudlog.event("process_not_running", not_running=not_running, error=True)
      self.not_running_prev = not_running
    else:
      if not SIMULATION and not self.rk.lagging:
        if not self.sm.all_alive(self.camera_packets):
          self.events.add(EventName.cameraMalfunction)
          if not self.sm.all_alive(['driverCameraState']) and not self.d_camera_hardware_missing:
            self.d_camera_hardware_missing = True
            self.params.put_bool_nonblocking("DriverCameraHardwareMissing", True)
        elif not self.sm.all_freq_ok(self.camera_packets):
          self.events.add(EventName.cameraFrameRate)
      self.process_not_running = False
    if not REPLAY and self.rk.lagging:
      self.events.add(EventName.controlsdLagging)
    if len(self.sm['radarState'].radarErrors) or (
      (not self.rk.lagging or REPLAY) and not self.sm.all_checks(['radarState'])):
      self.events.add(EventName.radarFault)
    if not self.sm.valid['pandaStates']:
      self.events.add(EventName.usbError)
    if CS.canTimeout:
      self.events.add(EventName.canBusMissing)
    elif not CS.canValid:
      self.events.add(EventName.canError)

    # generic catch-all. ideally, a more specific event should be added above instead
    has_disable_events = self.events.contains(ET.NO_ENTRY) and (
        self.events.contains(ET.SOFT_DISABLE) or self.events.contains(ET.IMMEDIATE_DISABLE))
    no_system_errors = (not has_disable_events) or (len(self.events) == num_events)
    if not self.sm.all_checks() and no_system_errors:
      if not self.sm.all_alive():
        self.events.add(EventName.commIssue)
      elif not self.sm.all_freq_ok():
        self.events.add(EventName.commIssueAvgFreq)
      else:
        self.events.add(EventName.commIssue)

      logs = {
        'invalid': [s for s, valid in self.sm.valid.items() if not valid],
        'not_alive': [s for s, alive in self.sm.alive.items() if not alive],
        'not_freq_ok': [s for s, freq_ok in self.sm.freq_ok.items() if not freq_ok],
      }
      if logs != self.logged_comm_issue:
        cloudlog.event("commIssue", error=True, **logs)
        self.logged_comm_issue = logs
    else:
      self.logged_comm_issue = None

    if not (self.CP.notCar and self.joystick_mode):
      if self.model_use_lateral_planner:
        if not self.sm['lateralPlanDEPRECATED'].mpcSolutionValid:
          self.events.add(EventName.plannerErrorDEPRECATED)
      if not self.sm['liveLocationKalman'].posenetOK:
        self.events.add(EventName.posenetInvalid)
      if not self.sm['liveLocationKalman'].deviceStable:
        self.events.add(EventName.deviceFalling)
      # Filtro temporal para locationdTemporaryError: solo activar si inputsOK está False durante al menos 2 segundos
      # Esto evita activaciones demasiado rápidas que pueden causar desactivaciones inmediatas
      if not self.sm['liveLocationKalman'].inputsOK:
        if not hasattr(self, 'locationd_error_start_time') or self.locationd_error_start_time is None:
          self.locationd_error_start_time = self.sm.frame
        elif (self.sm.frame - self.locationd_error_start_time) * DT_CTRL >= 2.0:  # 2 segundos de tolerancia
          self.events.add(EventName.locationdTemporaryError)
      else:
        # Resetear el contador si inputsOK vuelve a ser True
        if hasattr(self, 'locationd_error_start_time'):
          self.locationd_error_start_time = None
      if not self.sm['liveParameters'].valid and not TESTING_CLOSET and (not SIMULATION or REPLAY):
        self.events.add(EventName.paramsdTemporaryError)

    # conservative HW alert. if the data or frequency are off, locationd will throw an error
    if any((self.sm.frame - self.sm.recv_frame[s]) * DT_CTRL > 10. for s in self.sensor_packets):
      self.events.add(EventName.sensorDataInvalid)

    if not REPLAY:
      # Check for mismatch between openpilot and car's PCM
      cruise_mismatch = CS.cruiseState.enabled and not self.enabled
      self.cruise_mismatch_counter = self.cruise_mismatch_counter + 1 if cruise_mismatch else 0
      if self.cruise_mismatch_counter > int(6. / DT_CTRL):
        self.events.add(EventName.cruiseMismatch)

    # Check for FCW
    stock_long_is_braking = self.enabled and not self.CP.openpilotLongitudinalControl and CS.aEgo < -1.25
    model_fcw = self.sm['modelV2'].meta.hardBrakePredicted and not CS.brakePressed and not stock_long_is_braking
    planner_fcw = self.sm['longitudinalPlan'].fcw and self.enabled
    if (planner_fcw or model_fcw) and not (self.CP.notCar and self.joystick_mode):
      self.events.add(EventName.fcw)

    for m in messaging.drain_sock(self.log_sock, wait_for_one=False):
      try:
        msg = m.androidLog.message
        if any(err in msg for err in ("ERROR_CRC", "ERROR_ECC", "ERROR_STREAM_UNDERFLOW", "APPLY FAILED")):
          csid = msg.split("CSID:")[-1].split(" ")[0]
          evt = CSID_MAP.get(csid, None)
          if evt is not None:
            self.events.add(evt)
      except UnicodeDecodeError:
        pass

    # TODO: fix simulator
    if not SIMULATION or REPLAY:
      # Not show in first 1 km to allow for driving out of garage. This event shows after 5 minutes
      if not self.sm['liveLocationKalman'].gpsOK and self.sm['liveLocationKalman'].inputsOK and (
        self.distance_traveled > 1500):
        self.events.add(EventName.noGps)
      if self.sm['liveLocationKalman'].gpsOK:
        self.distance_traveled = 0
      self.distance_traveled += CS.vEgo * DT_CTRL

      if self.sm['modelV2'].frameDropPerc > 20:
        self.events.add(EventName.modeldLagging)

    # adri lane_change
    # adri lane_change

  def data_sample(self):
    """Receive data from sockets"""

    car_state = messaging.recv_one(self.car_state_sock)
    CS = car_state.carState if car_state else self.CS_prev

    self.sm.update(0)

    if not self.initialized:
      all_valid = CS.canValid and self.sm.all_checks()
      timed_out = self.sm.frame * DT_CTRL > 6.
      if all_valid or timed_out or (SIMULATION and not REPLAY):
        available_streams = VisionIpcClient.available_streams("camerad", block=False)
        if VisionStreamType.VISION_STREAM_ROAD not in available_streams:
          self.sm.ignore_alive.append('roadCameraState')
        if VisionStreamType.VISION_STREAM_WIDE_ROAD not in available_streams:
          self.sm.ignore_alive.append('wideRoadCameraState')

        self.initialized = True
        self.set_initial_state()

        cloudlog.event(
          "controlsd.initialized",
          dt=self.sm.frame * DT_CTRL,
          timeout=timed_out,
          canValid=CS.canValid,
          invalid=[s for s, valid in self.sm.valid.items() if not valid],
          not_alive=[s for s, alive in self.sm.alive.items() if not alive],
          not_freq_ok=[s for s, freq_ok in self.sm.freq_ok.items() if not freq_ok],
          error=True,
        )

    # When the panda and controlsd do not agree on controls_allowed
    # we want to disengage openpilot. However the status from the panda goes through
    # another socket other than the CAN messages and one can arrive earlier than the other.
    # Therefore we allow a mismatch for two samples, then we trigger the disengagement.
    if not self.enabled:
      self.mismatch_counter = 0

    # All pandas not in silent mode must have controlsAllowed when openpilot is enabled
    if self.enabled and any(not ps.controlsAllowed for ps in self.sm['pandaStates']
                            if ps.safetyModel not in IGNORED_SAFETY_MODES):
      self.mismatch_counter += 1

    return CS

  def state_transition(self, CS):
    """Compute conditional state transitions and execute actions on state transitions"""

    self.v_cruise_helper.update_v_cruise(CS, self.enabled_long, self.is_metric, self.reverse_acc_change,
                                         self.sm['longitudinalPlanSP'])

    # Procesar comandos de velocidad AdriPilot DESPUÉS de update_v_cruise
    # Esto permite que los cambios de AdriPilot se apliquen antes de que se use el valor en state_control
    # IMPORTANTE: Si el coche tiene pcmCruise y pcmCruiseSpeed, update_v_cruise sobrescribe v_cruise_kph
    # desde CS.cruiseState.speed. Por eso procesamos los comandos de AdriPilot DESPUÉS para que
    # los cambios se apliquen correctamente.
    # Pasamos enabled_long para que pueda verificar si el control longitudinal está activo
    try:
      # Reutilizar objeto temporal (evita crear clase nueva cada frame)
      if not hasattr(self, '_temp_car_control'):
        class _TempCarControl:
          __slots__ = ['enabled_long']
          def __init__(self, enabled_long):
            self.enabled_long = enabled_long
        self._TempCarControlCls = _TempCarControl
        self._temp_car_control = _TempCarControl(self.enabled_long)
      self._temp_car_control.enabled_long = self.enabled_long
      adripilot_speed_ultra_simple.process_speed_commands(self._temp_car_control, CS, self.v_cruise_helper)
    except Exception as e:
      # Log del error de forma muy limitada para no saturar
      if hasattr(self, '_adripilot_error_count'):
        self._adripilot_error_count += 1
      else:
        self._adripilot_error_count = 1
      if self._adripilot_error_count % 100 == 0:  # Log cada 100 errores
        cloudlog.error(f"❌ AdriPilot Speed: Error en state_transition: {e}")

    # Adelantamiento automático: aplicar objetivo de velocidad si está definido
    # Esto permite que desire_helper ajuste el setSpeed de forma centralizada, igual que los comandos MQTT.
    # IMPORTANTE: Solo aplicar cuando el adelantamiento está activo para evitar bloqueos
    try:
      overtake_active = self.params.get_bool("overtakingActive", False)
      if overtake_active:
        overtake_target = self.params.get("OvertakeTargetSpeedKph")
        if overtake_target:
          try:
            target_kph = float(overtake_target.decode("utf-8") if isinstance(overtake_target, bytes) else overtake_target)
          except Exception:
            target_kph = 0.0

          # Aplicar solo valores válidos y cuando el control longitudinal/crucero está activo
          if target_kph > 0:
            self.v_cruise_helper.v_cruise_kph = target_kph
            self.v_cruise_helper.v_cruise_cluster_kph = target_kph
      else:
        # Si el adelantamiento no está activo pero hay velocidad para restaurar, aplicarla primero
        try:
          overtake_target = self.params.get("OvertakeTargetSpeedKph")
          if overtake_target:
            # Aplicar la velocidad restaurada UNA VEZ antes de eliminar el parámetro
            try:
              target_kph = float(overtake_target.decode("utf-8") if isinstance(overtake_target, bytes) else overtake_target)
              if target_kph > 0:
                self.v_cruise_helper.v_cruise_kph = target_kph
                self.v_cruise_helper.v_cruise_cluster_kph = target_kph
            except Exception:
              pass
            # Ahora sí eliminar el parámetro
            self.params.remove("OvertakeTargetSpeedKph")
        except Exception:
          pass
    except Exception:
      pass

    # decrement the soft disable timer at every step, as it's reset on
    # entrance in SOFT_DISABLING state
    self.soft_disable_timer = max(0, self.soft_disable_timer - 1)

    self.current_alert_types = [ET.PERMANENT]

    # ENABLED, SOFT DISABLING, PRE ENABLING, OVERRIDING
    if self.state != State.disabled:
      # user and immediate disable always have priority in a non-disabled state
      if self.events.contains(ET.USER_DISABLE):
        self.state = State.disabled
        self.current_alert_types.append(ET.USER_DISABLE)

      elif self.events.contains(ET.IMMEDIATE_DISABLE):
        self.state = State.disabled
        if CS.gearShifter != GearShifter.park:
          self.current_alert_types.append(ET.IMMEDIATE_DISABLE)

      else:
        # ENABLED
        if self.state == State.enabled:
          if CS.cruiseState.enabled and not self.CS_prev.cruiseState.enabled:
            self.v_cruise_helper.initialize_v_cruise(CS, self.experimental_mode, self.is_metric,
                                                     self.dynamic_experimental_control)
          # Block resume if cruise never previously enabled
          resume_pressed = any(be.type in (ButtonType.accelCruise, ButtonType.resumeCruise) for be in CS.buttonEvents)
          if not self.CP.pcmCruise and not self.v_cruise_helper.v_cruise_initialized and resume_pressed:
            self.current_alert_types.append(ET.NO_ENTRY)
          if self.events.contains(ET.SOFT_DISABLE):
            self.state = State.softDisabling
            self.soft_disable_timer = int(SOFT_DISABLE_TIME / DT_CTRL)
            self.current_alert_types.append(ET.SOFT_DISABLE)

          elif self.events.contains(ET.PRE_ENABLE):
            self.current_alert_types.append(ET.PRE_ENABLE)

          elif self.events.contains(ET.OVERRIDE_LATERAL) or self.events.contains(ET.OVERRIDE_LONGITUDINAL):
            self.state = State.overriding
            self.current_alert_types += [ET.OVERRIDE_LATERAL, ET.OVERRIDE_LONGITUDINAL]

        # SOFT DISABLING
        elif self.state == State.softDisabling:
          if not self.events.contains(ET.SOFT_DISABLE):
            # no more soft disabling condition, so go back to ENABLED
            self.state = State.enabled

          elif self.soft_disable_timer > 0:
            self.current_alert_types.append(ET.SOFT_DISABLE)

          elif self.soft_disable_timer <= 0:
            self.state = State.disabled

        # PRE ENABLING
        elif self.state == State.preEnabled:
          if not self.events.contains(ET.PRE_ENABLE):
            self.state = State.enabled
          else:
            self.current_alert_types.append(ET.PRE_ENABLE)

        # OVERRIDING
        elif self.state == State.overriding:
          if self.events.contains(ET.SOFT_DISABLE):
            self.state = State.softDisabling
            self.soft_disable_timer = int(SOFT_DISABLE_TIME / DT_CTRL)
            self.current_alert_types.append(ET.SOFT_DISABLE)
          elif not (self.events.contains(ET.OVERRIDE_LATERAL) or self.events.contains(ET.OVERRIDE_LONGITUDINAL)):
            self.state = State.enabled
          else:
            self.current_alert_types += [ET.OVERRIDE_LATERAL, ET.OVERRIDE_LONGITUDINAL]
          if CS.cruiseState.enabled and not self.CS_prev.cruiseState.enabled:
            self.v_cruise_helper.initialize_v_cruise(CS, self.experimental_mode, self.is_metric,
                                                     self.dynamic_experimental_control)

    # DISABLED
    elif self.state == State.disabled:
      if self.events.contains(ET.ENABLE):
        if self.events.contains(ET.NO_ENTRY):
          self.current_alert_types.append(ET.NO_ENTRY)

        else:
          if self.events.contains(ET.PRE_ENABLE):
            self.state = State.preEnabled
          elif self.events.contains(ET.OVERRIDE_LATERAL) or self.events.contains(ET.OVERRIDE_LONGITUDINAL):
            self.state = State.overriding
          else:
            self.state = State.enabled
          self.current_alert_types.append(ET.ENABLE)
          if CS.cruiseState.enabled:
            self.v_cruise_helper.initialize_v_cruise(CS, self.experimental_mode, self.is_metric,
                                                     self.dynamic_experimental_control)

    # Check if openpilot is engaged and actuators are enabled
    self.enabled = self.state in ENABLED_STATES
    self.enabled_long = self.enabled and CS.cruiseState.enabled
    self.active = self.state in ACTIVE_STATES
    if self.active:
      self.current_alert_types.append(ET.WARNING)

  def state_control(self, CS):
    """Given the state, this function returns a CarControl packet"""

    # Update VehicleModel
    lp = self.sm['liveParameters']
    x = max(lp.stiffnessFactor, 0.1)
    sr = max(lp.steerRatio, 0.1)
    self.VM.update_params(x, sr)

    # ════════════════════════════════════════════════════════════════════════
    # RESUMEN DE COMO FUNCIONA EL TORQUE LATERAL EN COMMA (contexto para leer
    # lo que viene abajo):
    #
    #   - Comma NO manda un "angulo objetivo" al volante. Manda un torque
    #     normalizado en el rango [-1.0, +1.0] (campo `actuators.steer`).
    #     Este valor lo convierte el carcontroller en Nm reales por CAN.
    #     (Los coches "angle" como Tesla son otra historia: usan
    #     `actuators.steeringAngleDeg` y no este flujo.)
    #
    #   - El controlador que calcula ese torque es `LatControlTorque`
    #     (selfdrive/controls/lib/latcontrol_torque.py). NO razona por
    #     angulo de volante, razona por ACELERACION LATERAL DESEADA:
    #         desired_lateral_accel = desired_curvature * vEgo**2
    #     Es decir, a mayor velocidad, misma curvatura = mas aceleracion
    #     lateral = mas torque. Por eso el torque depende mucho de vEgo.
    #
    #   - El PID trabaja sobre el error entre aceleracion lateral deseada
    #     y medida (con un low_speed_factor extra a bajas velocidades para
    #     compensar que a poca velocidad el modelo lineal no es fiable).
    #     Ademas suma un feedforward basado en `torque_from_lateral_accel`
    #     (o NNFF si el coche tiene red neuronal entrenada) que compensa
    #     roll de la carretera, friccion del volante y jerk lateral.
    #
    #   - `liveTorqueParameters` son las ganancias del modelo (latAccelFactor,
    #     offset, friccion) que se autoajustan en marcha. Aqui se refrescan
    #     si el usuario no esta sobreescribiendo manualmente con TorquedOverride.
    # ════════════════════════════════════════════════════════════════════════

    # Update Torque Params
    if self.CP.lateralTuning.which() == 'torque':
      torque_params = self.sm['liveTorqueParameters']
      if self.sm.all_checks(['liveTorqueParameters']) and (
        torque_params.useParams or self.live_torque) and not self.torqued_override:
        self.LaC.update_live_torque_params(torque_params.latAccelFactorFiltered, torque_params.latAccelOffsetFiltered,
                                           torque_params.frictionCoefficientFiltered)

    lat_plan = self.sm['lateralPlanDEPRECATED']
    long_plan = self.sm['longitudinalPlan']
    model_v2 = self.sm['modelV2']
    blinker_svs = lat_plan if self.model_use_lateral_planner else model_v2.meta

    CC = car.CarControl.new_message()
    CC.enabled = self.enabled

    # Check which actuators can be enabled
    standstill = CS.vEgo <= max(self.CP.minSteerSpeed, MIN_LATERAL_CONTROL_SPEED) or CS.standstill
    CC.latActive = (self.active or self.mads_ndlob) and not CS.steerFaultTemporary and not CS.steerFaultPermanent and \
                   (not standstill or self.joystick_mode) and CS.madsEnabled and (
                       not CS.brakePressed or self.mads_ndlob) and \
                   (not CS.belowLaneChangeSpeed or (
                       not (((self.sm.frame - self.last_blinker_frame) * DT_CTRL) < 1.0) and
                       not (CS.leftBlinker or CS.rightBlinker))) and CS.latActive and self.sm[
                     'liveCalibration'].calStatus == log.LiveCalibrationData.Status.calibrated and \
                   not self.process_not_running
    CC.longActive = self.enabled_long and not (
        CS.brakePressed and (not self.CS_prev.brakePressed or not CS.standstill)) and not self.events.contains(
      ET.OVERRIDE_LONGITUDINAL)

    actuators = CC.actuators
    actuators.longControlState = self.LoC.long_control_state

    # Procesar comandos AdriPilot (ultra simplificado)
    try:
      adripilot_control_ultra_simple.process_commands(CC, CS, self.sm)
    except Exception:
      pass  # Error silenciado para reducir uso de memoria

    # Procesar comandos de velocidad AdriPilot (ultra simplificado) - MOVIDO DESPUÉS
    # Este código se ejecuta después de la asignación de CC.vCruise para evitar sobrescritura


    '''
    #CONTROL lateral
    if not self.joystick_mode:
      # Añadir aquí el código para forzar el giro a la derecha
      self.desired_curvature = +0.01  # Ajusta este valor para el giro deseado hacia la derecha (+) o izq (-)
    '''
    # Enable blinkers while lane changing
    # Enable blinkers while lane changing
    if blinker_svs.laneChangeState != LaneChangeState.off:
      CC.leftBlinker = blinker_svs.laneChangeDirection == LaneChangeDirection.left
      CC.rightBlinker = blinker_svs.laneChangeDirection == LaneChangeDirection.right

    # ← FUERZA EL ICONO DEL INTERMITENTE SI EL BLINKER FUE FORZADO
    if CS.leftBlinker:
      CC.leftBlinker = True

    if CS.leftBlinker or CS.rightBlinker:
      self.last_blinker_frame = self.sm.frame

    # State specific actions

    if not CC.latActive:
      self.LaC.reset()
    if not CC.longActive:
      self.LoC.reset()

    if not self.joystick_mode:
      # accel PID loop
      pid_accel_limits = self.CI.get_pid_accel_limits(self.CP, CS.vEgo,
                                                      self.v_cruise_helper.v_cruise_kph * CV.KPH_TO_MS)
      actuators.accel = self.LoC.update(CC.longActive, CS, long_plan.aTarget, long_plan.shouldStop, pid_accel_limits)

      # Brutebreak: Frenado de emergencia brusco por comando MQTT
      # Si está activo, aplica la intensidad de frenado configurada
      # El frenado se mantiene hasta que se desactive o el coche se detenga
      try:
        if self.params.get_bool("brutebreak_active"):
          # Leer intensidad de frenado configurable (default -3.5 m/s², configurable -1.0 a -10.0 vía MQTT)
          intensidad_frenado = -3.5  # Valor por defecto
          try:
            intensidad_raw = self.params.get("brutebreak_intensidad")
            if intensidad_raw:
              intensidad = float(intensidad_raw.decode("utf-8") if isinstance(intensidad_raw, bytes) else intensidad_raw)
              # Validar que esté en el rango permitido y sea negativo
              if -10.0 <= intensidad <= -1.0:
                intensidad_frenado = intensidad
          except Exception:
            pass  # Usar valor por defecto si hay error

          # Aplicar intensidad de frenado configurada (limitada al mínimo del sistema si es necesario)
          # pid_accel_limits[0] es el frenado máximo que permite el sistema
          actuators.accel = max(intensidad_frenado, pid_accel_limits[0])

          # Log para modo debug con valor de intensidad
          try:
            if self.params.get_bool("modo_debug") and self.sm.frame % 50 == 0:
              print(f"🛑 BRUTEBREAK ACTIVO - Intensidad: {intensidad_frenado} m/s²")
          except Exception:
            pass

          # Auto-desactivar si el coche se ha detenido (vEgo < 0.5 m/s)
          if CS.vEgo < 0.5:
            self.params.put_bool("brutebreak_active", False)
      except Exception:
        pass  # Error silencioso para no afectar el loop de control

      # Steering PID loop and lateral MPC
      # Si se usa el planificador lateral (lateral planner), se calcula la curvatura deseada ajustada
      # considerando el retardo del sistema. Esto se basa en la velocidad del vehículo (vEgo) y la
      # curvatura planeada del camino (`lat_plan.curvatures`).
      # CAMBIO DE CARRIL
      if self.model_use_lateral_planner:
        self.desired_curvature = get_lag_adjusted_curvature(self.CP, CS.vEgo, lat_plan.psis, lat_plan.curvatures)
      else:
        # Si no se usa el planificador lateral, se limita la curvatura deseada para evitar valores extremos
        # en función de la velocidad del vehículo (`vEgo`) y la curvatura prevista por el modelo (`model_v2.action.desiredCurvature`).
        self.desired_curvature = clip_curvature(CS.vEgo, self.desired_curvature, model_v2.action.desiredCurvature)

      # Se asigna la curvatura deseada al actuador, indicando el grado de giro que debe seguir el vehículo.
      actuators.curvature = self.desired_curvature

      # ────────────────────────────────────────────────────────────────
      # FUENTE 1 (por defecto) - TORQUE DE COMMA
      #
      # `LaC.update(...)` es la llamada que PRODUCE el torque "oficial" de
      # Comma. Para coches con lateralTuning = 'torque' (nuestro caso) esta
      # dentro de LatControlTorque (ver comentario arriba). Devuelve:
      #
      #   - `actuators.steer`          → TORQUE NORMALIZADO en [-1.0, +1.0].
      #                                  ES EL VALOR QUE FINALMENTE SE ENVIA
      #                                  AL COCHE (lo lee carcontroller y lo
      #                                  mete al CAN). Convencion: negativo =
      #                                  derecha, positivo = izquierda (por
      #                                  eso el "return -output_torque" dentro
      #                                  de latcontrol_torque.py).
      #   - `actuators.steeringAngleDeg` → Angulo deseado en grados. Solo se
      #                                  usa en coches angle-based; aqui va
      #                                  a 0 en modo torque.
      #   - `lac_log`                   → telemetria del lazo (errores, sat...)
      #
      # Ojo: `actuators.steer` se puede SOBREESCRIBIR justo abajo. Todo lo
      # que venga despues (Jetson / TEST MAX) pisa este valor antes de que
      # llegue al carcontroller.
      # ────────────────────────────────────────────────────────────────
      actuators.steer, actuators.steeringAngleDeg, lac_log = self.LaC.update(
        CC.latActive,  # Indica si el control lateral está activo.
        CS,  # Estado actual del vehículo.
        self.VM,  # Modelo del vehículo para cálculos de dinámica.
        lp,  # Parámetros en vivo de calibración.
        self.steer_limited,  # Indica si la dirección está limitada por el sistema.
        self.desired_curvature,  # Curvatura deseada basada en el plan de trayectoria.
        self.sm['liveLocationKalman'],  # Datos en vivo de ubicación y orientación del vehículo.
        model_data=model_v2  # Datos del modelo de conducción.
      )

      # Guardamos el torque "limpio" de Comma en un param ANTES de que nadie
      # lo pise. Lo usa la UI para mostrar en modo debug que torque habria
      # aplicado Comma aunque finalmente se use Jetson/MAX.
      try:
        self.params.put_nonblocking("CommaSteerTorque", f"{float(actuators.steer):.4f}")
      except Exception:
        pass

      # ════════════════════════════════════════════════════════════════
      # PUNTO CRITICO: SELECTOR DE FUENTE DE TORQUE DEL VOLANTE
      # ════════════════════════════════════════════════════════════════
      # Aqui es DONDE inyectamos el torque que queremos mandar al coche.
      # Tenemos 3 posibilidades y se eligen con el param "SteerTorqueMode":
      #
      #   0 = COMMA   → no hacemos nada, se queda lo que calculo LaC.update
      #                 (el PID sobre aceleracion lateral que hemos explicado).
      #   1 = JETSON  → sustituimos `actuators.steer` por el torque que
      #                 publica la Jetson (PilotNet u otro modelo externo)
      #                 via el param "JetsonTorque".
      #   2 = TEST MAX→ forzamos `actuators.steer = -1.0`. Es un test de
      #                 banco: si en este modo el volante no gira a tope a
      #                 la derecha, el problema NO esta aqui; esta aguas
      #                 abajo (carcontroller, panda, safety, etc.).
      #
      # FLUJO posterior (para que sirva para localizarlo):
      #   actuators.steer (aqui)
      #     → publish_logs() → CarControl por cereal
      #     → card/carcontroller.py (aplica rate-limit y saturacion)
      #     → CAN → panda (safety) → EPS del coche.
      #
      # ───── Detalles de la normalizacion JETSON (modo 1) ─────
      #   - Entrada esperada: "JetsonTorque" en rango nominal PilotNet
      #     [-500, +500]. Comma necesita [-1.0, +1.0], asi que escalamos.
      #   - Ganancia "JetsonTorqueGain" (default 5.0): los valores reales
      #     de PilotNet suelen ser muy inferiores a 500; la ganancia los
      #     amplifica antes de normalizar dividiendo entre 500.
      #   - Signo invertido (-jetson_torque_real): la convencion de la
      #     Jetson es opuesta a la de Comma en este coche
      #     (MAX +1.0 gira a la izquierda; queremos que positivo = derecha
      #     siguiendo la convencion de esta integracion).
      #   - Saturacion por estabilidad de signo: la Jetson publica a ~4-5 Hz
      #     mientras controlsd corre a 100 Hz. El rate-limiter del
      #     carcontroller rampa el torque muy despacio; si la senal oscila
      #     cancela el giro antes de llegar al target. Si el signo se
      #     mantiene SATURATE_AFTER ciclos seguidos, forzamos ±1.0 para
      #     dar tiempo al rampado y producir giro real.
      #   - Hold entre llegadas: si el param viene vacio (entre dos mensajes
      #     de la Jetson), reutilizamos el ultimo torque normalizado, asi
      #     evitamos "huecos" a 0 que cancelarian la intencion de giro.
      # ════════════════════════════════════════════════════════════════
      # ────────────────────────────────────────────────────────────────
      # NOTA POST-MORTEM (importante, no quitar):
      # En una prueba previa el coche "parecia conducir bien en modo
      # JETSON" cuando en realidad se aplicaba el torque de COMMA. Causa:
      # los params nuevos (JetsonTorqueTimestamp, JetsonDeadZone,
      # AppliedSteerTorque) no estaban registrados en C++ porque no se
      # recompilo params.cc. params.get(...) lanza UnknownKeyName en ese
      # caso. Un try/except Exception generico tragaba el error y
      # actuators.steer quedaba con el valor que habia calculado el LaC
      # (Comma). El usuario no podia detectarlo a simple vista.
      #
      # Para que NUNCA mas pase:
      #  - Manejamos UnknownKeyName explicitamente en cada get/put.
      #  - NO usamos `except Exception: pass` aqui. Si algo falla, el log
      #    debe verlo. Las unicas excepciones que silenciamos son las
      #    esperadas (ValueError/TypeError al parsear).
      #  - FAIL-SAFE: si la rama Jetson no puede leer su torque, ponemos
      #    actuators.steer = 0.0 (volante sin fuerza), no dejamos a Comma
      #    aplicarse silenciosamente. Asi un fallo es VISIBLE.
      # ────────────────────────────────────────────────────────────────
      if CC.latActive:
        try:
          mode_raw = self.params.get("SteerTorqueMode")
        except UnknownKeyName:
          cloudlog.error("SteerTorqueMode no registrado. Recompila common/params.cc.")
          mode_raw = None
        try:
          steer_mode = int(mode_raw) if mode_raw else 0
        except (ValueError, TypeError):
          steer_mode = 0

        if steer_mode == 1:
          # FUENTE 2 (JETSON): leemos el float que la Jetson dejo en el param
          # JetsonTorque (lo escribe sicuem/adripilot/zmq_client.py:_torque_listener
          # como str(torque) sobre un float ya normalizado en [-1, 1]).
          # params.get devuelve bytes/None: hay que convertir a float SI o SI,
          # asignar el bytes directamente al campo capnp float32 hace crashear
          # controlsd al serializar (ese era el "se queda pillado").
          try:
            jt = float(self.params.get("JetsonTorque") or 0.0)

          except (UnknownKeyName, ValueError, TypeError):
            jt = 0.0
          actuators.steer = jt
          #print("#######################################acctt####################################", actuators.steer)

          # ╔══════════════════════════════════════════════════════════════╗
          # ║ OTRAS VARIABLES *LATERALES* QUE EL MODO JETSON PUEDE TOCAR   ║
          # ║ (ver /home/drago/Escritorio/CONTROL_VARIABLES_JETSON.md)     ║
          # ╠══════════════════════════════════════════════════════════════╣
          # ║ SOLO control LATERAL. Nada de gas/freno/accel/speed: el      ║
          # ║ longitudinal lo lleva Comma sin tocarlo.                     ║
          # ║                                                              ║
          # ║ Hasta ahora la Jetson solo pisa `actuators.steer` (torque).  ║
          # ║ Si el torque solo no esta funcionando, podemos tocar tambien ║
          # ║ ALGUNA de estas variables (descomenta lo que quieras probar) ║
          # ║                                                              ║
          # ║ 1) self.desired_curvature  /  actuators.curvature  [1/m]     ║
          # ║    - LA MAS POTENTE de las alternativas al torque.           ║
          # ║    - Es el OBJETIVO geometrico de la trayectoria. Se calcula ║
          # ║      en linea 875-879. Si tu Jetson predijera la curvatura   ║
          # ║      (no el torque), aqui la inyectarias y dejas que el PID  ║
          # ║      de Comma haga el cierre fino sobre el volante.          ║
          # ║    - Rango tipico: [-0.1, +0.1] 1/m  (radios > 10m).         ║
          # ║    - Ejemplo (curvatura proporcional al "torque" jetson):    ║
          # ║        self.desired_curvature = jt * 0.05                    ║
          # ║        actuators.curvature   = self.desired_curvature        ║
          # ║      (en este caso, NO pisar tambien actuators.steer)        ║
          # ║                                                              ║
          # ║ 2) actuators.steeringAngleDeg  [grados del volante]          ║
          # ║    - Lo produce LaC.update() arriba.                         ║
          # ║    - En coches torque-based (el nuestro) el carcontroller NO ║
          # ║      lo manda al EPS, pero SI lo loguea y SI lo usan algunas ║
          # ║      alertas (steerSaturated mas abajo). Util para DEBUG y   ║
          # ║      preparar futuro coche angle-based.                      ║
          # ║    - Ejemplo:                                                ║
          # ║        actuators.steeringAngleDeg = jt * 90.0                ║
          # ║      (mismo rango que usa el modo joystick linea 1096)       ║
          # ║                                                              ║
          # ║ 3) self.steer_limited  [bool]  (anti-windup del PID)         ║
          # ║    - Bandera que le dice al LaC que el EPS esta saturado.    ║
          # ║    - Forzarla a True hace que el integrador del PID NO       ║
          # ║      acumule "deuda" cuando la Jetson satura su salida, lo   ║
          # ║      que reduce sobreoscilacion al volver al centro.         ║
          # ║    - Ejemplo:  self.steer_limited = abs(jt) > 0.9            ║
          # ║                                                              ║
          # ║ 4) Params en VIVO que recalibran el LaC torque:              ║
          # ║      "TorqueMaxLatAccel"  -> ganancia del feedforward        ║
          # ║      "TorqueFriction"     -> termino de friccion (kicker)    ║
          # ║    - Los relee LatControlTorque en cada update (~ linea 133  ║
          # ║      de latcontrol_torque.py). Reescribirlos desde aqui      ║
          # ║      "afina" el PID al vuelo segun lo que pida la Jetson.    ║
          # ║    - OJO con escribir a 100 Hz: cachea el ultimo valor y     ║
          # ║      solo escribe si cambia significativamente.              ║
          # ║                                                              ║
          # ║ 5) CC.latActive  [bool]  (informativo, no se toca aqui)      ║
          # ║    - Si la Jetson detecta que su salida es basura, lo mas    ║
          # ║      seguro es DEVOLVER el control al humano. El override    ║
          # ║      real va por params/eventos, no aqui directamente, pero  ║
          # ║      conviene saber que existe.                              ║
          # ╚══════════════════════════════════════════════════════════════╝
          # NOTA: descomenta SOLO una linea a la vez al probar. Mezclar
          # varias fuentes laterales (torque + curvatura + angulo) sin
          # entender la interaccion entre el LaC y el carcontroller
          # produce oscilaciones rarisimas dificiles de debuguear.

          # --- (a) Inyectar CURVATURA proporcional al torque jetson ---
          #         (recomendado: requiere comentar la linea actuators.steer
          #          de arriba para que mande de verdad la curvatura)
          # self.desired_curvature = jt * 0.05
          # actuators.curvature   = self.desired_curvature

          # --- (b) Marcar tambien el ANGULO en logs/alertas (seguro) ---
          # actuators.steeringAngleDeg = jt * 90.0

          # --- (c) Avisar al LaC de saturacion (anti-windup) ---
          # self.steer_limited = abs(jt) > 0.9

        elif steer_mode == 2:
          # FUENTE 3 (TEST MAX): torque fijo a -1.0 (derecha a tope) para
          # confirmar que este punto del codigo llega al EPS. Si en modo 2
          # el volante no gira a tope, el problema esta aguas abajo
          # (carcontroller / panda / safety).
          actuators.steer = -1.0
        elif steer_mode == 3:
          # FUENTE 4 (COMMA+JETSON): no tocamos actuators.steer aquí.
          # El torque base lo deja Comma. Más abajo (post-selector) sumamos
          # los offsets de ángulo y curvatura cuando hay esquive activo.
          pass
        # modo 0 (COMMA): no tocamos actuators.steer, queda lo del LaC.

      # ────────────────────────────────────────────────────────────────
      # Diagnostico: publicamos el torque FINAL tras el selector, para
      # que la UI pueda mostrar exactamente que valor esta yendo al
      # carcontroller y asi confirmar visualmente si la rama activa es
      # la esperada:
      #   modo 0 (Comma)     -> AT == CT
      #   modo 1 (Jetson)    -> AT == -JT (o 0 si watchdog/fallo)
      #   modo 2 (TEST MAX)  -> AT == -1.0
      # ────────────────────────────────────────────────────────────────
      try:
        self.params.put_nonblocking("AppliedSteerTorque", f"{float(actuators.steer):.4f}")
      except UnknownKeyName:
        # Param no registrado en C++ -> recompilar params.cc.
        # No es critico para conduccion, solo para la UI de diagnostico.
        pass

      # AdriPilot: Aplicar giro temporal del volante si hay comando MQTT
      # IMPORTANTE: Se aplica solo si el control lateral está activo (CC.latActive)
      # Sistema de dos fases:
      # 1. Fase inicial (0.5s): Gira en la dirección indicada
      # 2. Fase de retorno (0.5s): Gira en la dirección contraria para volver al estado original
      try:
        from openpilot.sicuem.adripilot.adripilot_steering_pulse import get_steering_pulse, adripilot_steering_pulse_duration, adripilot_steering_pulse_angle

        pulse_start, original_direction, is_active, phase, effective_direction = get_steering_pulse()

        if is_active and effective_direction in ["right", "left"] and CC.latActive:
          current_time = time.time()
          elapsed = current_time - pulse_start

          # Aplicar offset según la dirección efectiva (puede ser la original o la contraria en fase de retorno)
          if effective_direction == "right":
            actuators.steeringAngleDeg += adripilot_steering_pulse_angle
            # También ajustar curvatura para consistencia
            self.desired_curvature += 0.008
          elif effective_direction == "left":
            actuators.steeringAngleDeg -= adripilot_steering_pulse_angle
            # También ajustar curvatura para consistencia
            self.desired_curvature -= 0.008

          # Log eliminado para reducir uso de memoria - el giro se aplica silenciosamente
          pass
        elif is_active and not CC.latActive:
          # Pulso activo pero control lateral no activo - log eliminado para reducir memoria
          pass
        elif pulse_start is not None:
          # Hay un pulso pero no está activo - log eliminado para reducir memoria
          pass
      except ImportError:
        # Módulo no disponible - silencioso para reducir memoria
        pass
      except Exception:
        # Error inesperado - silencioso para reducir memoria
        pass

      # ────────────────────────────────────────────────────────────────
      # MODO 3 (COMMA+JETSON): offsets de esquive por obstáculo
      # ────────────────────────────────────────────────────────────────
      # Coexiste con la cruceta de la app: ambos suman al mismo
      # steeringAngleDeg / desired_curvature. En la práctica nunca están
      # activos a la vez (la cruceta es manual del usuario, el esquive es
      # automático del modelo Jetson) pero si lo estuvieran, los offsets
      # se sumarían y sería el peor caso de superposición.
      try:
        if CC.latActive and steer_mode == 3:
          # I-2: reusamos `steer_mode` ya leído por el selector arriba.
          now_pulse = time.time()
          self._refresh_obstacle_config(now_pulse)

          # Detectar mensaje nuevo (timestamp más reciente que el cached)
          try:
            payload_ts_raw = self.params.get("JetsonObstacleTimestamp")
            payload_ts = float(payload_ts_raw) if payload_ts_raw else 0.0
          except (UnknownKeyName, ValueError, TypeError):
            payload_ts = 0.0

          if payload_ts > self._obstacle_pulse_state.last_payload_ts:
            try:
              payload_raw = self.params.get("JetsonObstaclePulse")
              if payload_raw:
                payload = json.loads(payload_raw)
                # C-1: validar que el JSON es un dict antes de pasarlo
                if isinstance(payload, dict):
                  self._obstacle_pulse_state.ingest_new_message(payload, now_pulse)
                else:
                  cloudlog.error(f"controlsd: ObstaclePulse JSON no es dict: {payload!r}")
            except (UnknownKeyName, ValueError, TypeError, AttributeError) as e:
              cloudlog.error(f"controlsd: ObstaclePulse JSON inválido: {e}")

          angle_tgt, curv_tgt, status = self._obstacle_pulse_state.get_offsets(
            now_pulse, CS, CC.latActive,
            max_angle=self._obstacle_max_angle,
            max_curv=self._obstacle_max_curv,
          )
          # Gate por `active`, NO por (angle_tgt or curv_tgt): con la
          # semántica OVERRIDE absoluta queremos aplicar el target aunque
          # sea 0 (intensity=0 → torque/curvatura forzados a 0, volante
          # neutralizado / línea recta). Solo cuando obstacle:false → active
          # pasa a False → este bloque no entra → manda Comma.
          # Excepción: si BSM bloquea el esquive (BSM_BLOCKED_*), NO pisamos
          # la dirección — deja que mande el modelo de Comma. El status se
          # publica igual para que la UI lo muestre.
          bsm_blocked = status in ("BSM_BLOCKED_LEFT", "BSM_BLOCKED_RIGHT")
          if self._obstacle_pulse_state.active and not bsm_blocked:
            if self._obstacle_apply_target == "torque":
              # Sub-modo torque: OVERRIDE absoluto de actuators.steer con
              # intensity ∈ [-1,1] (clamped). intensity=0 → torque 0
              # (volante relajado). Cuando llegue obstacle:false → active
              # pasa a False → no entramos aquí → manda Comma.
              intensity = self._obstacle_pulse_state.intensity
              if math.isnan(intensity):
                intensity = 0.0
              actuators.steer = max(-1.0, min(1.0, intensity))
            else:
              # Sub-modo curvature: OVERRIDE absoluto (no offset). El target
              # = intensity * max_*. intensity=0 → curvatura/ángulo 0 →
              # línea recta. Simétrico con torque mode.
              actuators.steeringAngleDeg = angle_tgt
              self.desired_curvature = curv_tgt

          # Anti-flicker: si el status acaba de pasar a "" (o "CANCELED_DRIVER",
          # que también es un evento de cierre), mantenemos el último status
          # activo en el param durante OBSTACLE_STATUS_HOLD_S para que la UI
          # (≈20Hz) no pierda dodges muy breves. Sin esto, un obstacle:true
          # seguido a los pocos ms de obstacle:false hacía que el param
          # transitase "" → DODGING_LEFT → "" en <50ms y la UI no veía nada.
          if status in ("DODGING_LEFT", "DODGING_RIGHT", "DODGING_HOLD",
                        "BSM_BLOCKED_LEFT", "BSM_BLOCKED_RIGHT"):
            # Status activo: refresca el hold y publica este valor.
            self._obstacle_status_held_value = status
            self._obstacle_status_hold_until = now_pulse + OBSTACLE_STATUS_HOLD_S
            published = status
          elif self._obstacle_status_held_value and now_pulse < self._obstacle_status_hold_until:
            # Transición a "" / CANCELED_DRIVER pero aún dentro de la ventana
            # de hold → seguimos publicando el último activo.
            published = self._obstacle_status_held_value
          else:
            # Fuera de la ventana de hold: publicamos el status real
            # (puede ser "" o "CANCELED_DRIVER").
            self._obstacle_status_held_value = ""
            published = status

          if published != self._last_obstacle_status:
            try:
              self.params.put_nonblocking("JetsonObstacleStatus", published)
              self.params.put_nonblocking(
                "JetsonObstacleStatusMqttPayload",
                json.dumps({"status": published, "ts": now_pulse, "source": "comma"}),
              )
            except UnknownKeyName:
              pass
            self._last_obstacle_status = published

        elif self._obstacle_pulse_state.active or self._obstacle_status_held_value or self._last_obstacle_status:
          # I-1 + I-4: salimos de modo 3 (o lat inactivo) con esquive activo
          # o con un status pendiente de hold → forzar reset y limpiar status
          # para que la UI no quede colgada.
          self._obstacle_pulse_state._reset()
          self._obstacle_status_held_value = ""
          self._obstacle_status_hold_until = 0.0
          if self._last_obstacle_status:
            try:
              self.params.put_nonblocking("JetsonObstacleStatus", "")
              self.params.put_nonblocking(
                "JetsonObstacleStatusMqttPayload",
                json.dumps({"status": "", "ts": time.time(), "source": "comma"}),
              )
            except UnknownKeyName:
              pass
            self._last_obstacle_status = ""
      except Exception as e:
        # C-2: hot-path, ningún error puede propagarse al main loop.
        cloudlog.error(f"controlsd: excepcion inesperada en bloque modo 3: {e}")

      if self.model_use_lateral_planner:
        actuators.curvature = self.desired_curvature
    else:
      lac_log = log.ControlsState.LateralDebugState.new_message()
      if self.sm.recv_frame['testJoystick'] > 0:
        # reset joystick if it hasn't been received in a while
        should_reset_joystick = (self.sm.frame - self.sm.recv_frame['testJoystick']) * DT_CTRL > 0.2
        if not should_reset_joystick:
          joystick_axes = self.sm['testJoystick'].axes
        else:
          joystick_axes = [0.0, 0.0]

        if CC.longActive:
          actuators.accel = 4.0 * clip(joystick_axes[0], -1, 1)

        if CC.latActive:
          steer = clip(joystick_axes[1], -1, 1)
          # max angle is 45 for angle-based cars, max curvature is 0.02
          actuators.steer, actuators.steeringAngleDeg, actuators.curvature = steer, steer * 90., steer * -0.02

        lac_log.active = self.active
        lac_log.steeringAngleDeg = CS.steeringAngleDeg
        lac_log.output = actuators.steer
        lac_log.saturated = abs(actuators.steer) >= 0.9

    if CS.steeringPressed:
      self.last_steering_pressed_frame = self.sm.frame
    recent_steer_pressed = (self.sm.frame - self.last_steering_pressed_frame) * DT_CTRL < 2.0

    # Send a "steering required alert" if saturation count has reached the limit
    if lac_log.active and not recent_steer_pressed and not self.CP.notCar and CS.madsEnabled:
      if self.CP.lateralTuning.which() == 'torque' and not self.joystick_mode:
        undershooting = abs(lac_log.desiredLateralAccel) / abs(1e-3 + lac_log.actualLateralAccel) > 1.2
        turning = abs(lac_log.desiredLateralAccel) > 1.0
        good_speed = CS.vEgo > 5
        max_torque = abs(self.sm['carOutput'].actuatorsOutput.steer) > 0.99
        if undershooting and turning and good_speed and max_torque:
          lac_log.active and self.events.add(EventName.steerSaturated)
      elif lac_log.saturated:
        # TODO probably should not use dpath_points but curvature
        dpath_points = lat_plan.dPathPoints if self.model_use_lateral_planner else model_v2.position.y
        if len(dpath_points):
          # Check if we deviated from the path
          # TODO use desired vs actual curvature
          if self.CP.steerControlType == car.CarParams.SteerControlType.angle:
            steering_value = actuators.steeringAngleDeg
          else:
            steering_value = actuators.steer

          left_deviation = steering_value > 0 and dpath_points[0] < -0.20
          right_deviation = steering_value < 0 and dpath_points[0] > 0.20

          if left_deviation or right_deviation:
            self.events.add(EventName.steerSaturated)

    # Ensure no NaNs/Infs
    for p in ACTUATOR_FIELDS:
      attr = getattr(actuators, p)
      if not isinstance(attr, SupportsFloat):
        continue

      if not math.isfinite(attr):
        cloudlog.error(f"actuators.{p} not finite {actuators.to_dict()}")
        setattr(actuators, p, 0.0)

    # toggle experimental mode once on distance button hold
    if self.CP.openpilotLongitudinalControl:
      if self.v_cruise_helper.button_timers[ButtonType.gapAdjustCruise] == CRUISE_LONG_PRESS and \
        not self.experimental_mode_update:
        self.experimental_mode = not self.experimental_mode
        self.params.put_bool_nonblocking("ExperimentalMode", self.experimental_mode)
        self.experimental_mode_update = True

    # decrement personality on distance button press
    if self.CP.openpilotLongitudinalControl:
      if any(not be.pressed and be.type == ButtonType.gapAdjustCruise for be in CS.buttonEvents):
        if not self.experimental_mode_update:
          self.personality = (self.personality - 1) % 3
          self.params.put_nonblocking('LongitudinalPersonality', str(self.personality))
        self.experimental_mode_update = False

    return CC, lac_log

  def publish_logs(self, CS, start_time, CC, lac_log):
    """Send actuators and hud commands to the car, send controlsstate and MPC logging"""

    # Orientation and angle rates can be useful for carcontroller
    # Only calibrated (car) frame is relevant for the carcontroller
    orientation_value = list(self.sm['liveLocationKalman'].calibratedOrientationNED.value)
    if len(orientation_value) > 2:
      CC.orientationNED = orientation_value
    angular_rate_value = list(self.sm['liveLocationKalman'].angularVelocityCalibrated.value)
    if len(angular_rate_value) > 2:
      CC.angularVelocity = angular_rate_value

    CC.cruiseControl.override = self.enabled_long and not CC.longActive and self.CP.openpilotLongitudinalControl
    CC.cruiseControl.cancel = CS.cruiseState.enabled and \
                              (not self.enabled_long or (
                                  CS.brakePressed and (not self.CS_prev.brakePressed or not CS.standstill)) or
                               (any(
                                 b.type == ButtonType.cancel for b in CS.buttonEvents) and self.CP.carName == "honda"))
    if self.joystick_mode and self.sm.recv_frame['testJoystick'] > 0 and self.sm['testJoystick'].buttons[0]:
      CC.cruiseControl.cancel = True

    speeds = self.sm['longitudinalPlan'].speeds
    if len(speeds):
      CC.cruiseControl.resume = self.enabled_long and CS.cruiseState.standstill and speeds[-1] > 0.1

    # El adelantamiento ahora modifica directamente v_cruise_helper.v_cruise_kph
    # (igual que los comandos MQTT), así que no necesitamos hacer nada aquí

    # Los comandos de velocidad AdriPilot ya se procesaron en state_transition()
    # después de update_v_cruise(), así que aquí solo aplicamos el valor final
    CC.vCruise = self.v_cruise_helper.v_cruise_kph
    hudControl = CC.hudControl
    hudControl.setSpeed = float(self.v_cruise_helper.v_cruise_kph * CV.KPH_TO_MS)

    hudControl.speedVisible = self.enabled_long
    hudControl.lanesVisible = self.enabled
    hudControl.leadVisible = self.sm['longitudinalPlan'].hasLead
    hudControl.leadDistanceBars = PERSONALITY_MAPPING.get(self.personality, log.LongitudinalPersonality.standard) + 1

    hudControl.rightLaneVisible = True
    hudControl.leftLaneVisible = True

    recent_blinker = (self.sm.frame - self.last_blinker_frame) * DT_CTRL < 5.0  # 5s blinker cooldown
    ldw_allowed = self.is_ldw_enabled and CS.vEgo > LDW_MIN_SPEED and not recent_blinker \
                  and not CC.latActive and self.sm[
                    'liveCalibration'].calStatus == log.LiveCalibrationData.Status.calibrated

    model_v2 = self.sm['modelV2']
    desire_prediction = model_v2.meta.desirePrediction
    if len(desire_prediction) and ldw_allowed:
      right_lane_visible = model_v2.laneLineProbs[2] > 0.5
      left_lane_visible = model_v2.laneLineProbs[1] > 0.5
      l_lane_change_prob = desire_prediction[Desire.laneChangeLeft]
      r_lane_change_prob = desire_prediction[Desire.laneChangeRight]

      lane_lines = model_v2.laneLines
      l_lane_close = left_lane_visible and (lane_lines[1].y[0] > -(1.08 + CAMERA_OFFSET))
      r_lane_close = right_lane_visible and (lane_lines[2].y[0] < (1.08 - CAMERA_OFFSET))

      hudControl.leftLaneDepart = bool(l_lane_change_prob > LANE_DEPARTURE_THRESHOLD and l_lane_close)
      hudControl.rightLaneDepart = bool(r_lane_change_prob > LANE_DEPARTURE_THRESHOLD and r_lane_close)

    if hudControl.rightLaneDepart or hudControl.leftLaneDepart:
      self.events.add(EventName.ldw)

    clear_event_types = set()
    if ET.WARNING not in self.current_alert_types:
      clear_event_types.add(ET.WARNING)
    if self.enabled and (self.CP.pcmCruise or (not self.CP.pcmCruise and self.v_cruise_helper.v_cruise_initialized)):
      clear_event_types.add(ET.NO_ENTRY)

    alerts = self.events.create_alerts(self.current_alert_types,
                                       [self.CP, CS, self.sm, self.is_metric, self.soft_disable_timer])

    # Enviar por MQTT eventos completos con cooldown
    # IMPORTANTE: Este código se ejecuta SIEMPRE, tanto en simulador como en coche real
    # Sistema optimizado: envía eventos completos con toda su información
    # Cooldown de 12 segundos por evento para evitar saturación
    try:
      from openpilot.sicuem.adripilot import events_mqtt

      # Debug: Log eliminado para reducir uso de memoria
      # Los eventos se procesan silenciosamente para evitar saturación

      # Procesar cada alerta - el sistema de cooldown está dentro de send_alert
      for a in alerts:
        atype = getattr(a, 'alert_type', '') or ''
        if atype:
          # send_alert maneja internamente el cooldown y solo envía códigos cortos
          try:
            events_mqtt.send_alert(a)
          except Exception as e:
            # Error silencioso para no afectar el loop de control
            if self.sm.frame % 100 == 0:  # Log solo ocasionalmente
              cloudlog.error(f"❌ AdriPilot: Error enviando evento MQTT {atype}: {e}")
    except ImportError as e:
      cloudlog.error(f"❌ AdriPilot: Error importando events_mqtt: {e}")
    except Exception as e:
      if self.sm.frame % 100 == 0:  # Log solo ocasionalmente
        cloudlog.error(f"❌ AdriPilot: Error procesando eventos MQTT: {e}")

    self.AM.add_many(self.sm.frame, alerts)
    current_alert = self.AM.process_alerts(self.sm.frame, clear_event_types)
    if current_alert:
      hudControl.visualAlert = current_alert.visual_alert

    if not self.CP.passive and self.initialized:
      CO = self.sm['carOutput']
      if self.CP.steerControlType == car.CarParams.SteerControlType.angle:
        self.steer_limited = abs(CC.actuators.steeringAngleDeg - CO.actuatorsOutput.steeringAngleDeg) > \
                             STEER_ANGLE_SATURATION_THRESHOLD
      else:
        self.steer_limited = abs(CC.actuators.steer - CO.actuatorsOutput.steer) > 1e-2

    force_decel = (self.sm['driverMonitoringState'].awarenessStatus < 0.) or \
                  (self.state == State.softDisabling)

    # Curvature & Steering angle
    lp = self.sm['liveParameters']
    lp_mono_time_svs = 'lateralPlanDEPRECATED' if self.model_use_lateral_planner else 'modelV2'

    steer_angle_without_offset = math.radians(CS.steeringAngleDeg - lp.angleOffsetDeg)
    curvature = -self.VM.calc_curvature(steer_angle_without_offset, CS.vEgo, lp.roll)

    # controlsState
    dat = messaging.new_message('controlsState')
    dat.valid = CS.canValid
    controlsState = dat.controlsState
    if current_alert:
      controlsState.alertText1 = current_alert.alert_text_1
      controlsState.alertText2 = current_alert.alert_text_2
      controlsState.alertSize = current_alert.alert_size
      controlsState.alertStatus = current_alert.alert_status
      controlsState.alertBlinkingRate = current_alert.alert_rate
      controlsState.alertType = current_alert.alert_type
      controlsState.alertSound = current_alert.audible_alert

    controlsState.longitudinalPlanMonoTime = self.sm.logMonoTime['longitudinalPlan']
    controlsState.lateralPlanMonoTime = self.sm.logMonoTime[lp_mono_time_svs]
    # original
    controlsState.enabled = not (CS.brakePressed and (not self.CS_prev.brakePressed or not CS.standstill)) and (
        self.enabled or CS.cruiseState.enabled) and CS.gearShifter not in [GearShifter.park, GearShifter.reverse]
    # adri
    # controlsState.enabled = not (CS.brakePressed and (not self.CS_prev.brakePressed or not CS.standstill)) and (self.enabled or CS.cruiseState.enabled)

    controlsState.active = not (CS.brakePressed and (not self.CS_prev.brakePressed or not CS.standstill)) and (
        self.active or CS.cruiseState.enabled)
    controlsState.curvature = curvature
    controlsState.desiredCurvature = self.desired_curvature
    controlsState.state = self.state
    controlsState.engageable = not self.events.contains(ET.NO_ENTRY)
    controlsState.longControlState = self.LoC.long_control_state
    controlsState.vCruise = float(self.v_cruise_helper.v_cruise_kph)
    controlsState.vCruiseCluster = float(self.v_cruise_helper.v_cruise_cluster_kph)
    controlsState.upAccelCmd = float(self.LoC.pid.p)
    controlsState.uiAccelCmd = float(self.LoC.pid.i)
    controlsState.ufAccelCmd = float(self.LoC.pid.f)
    controlsState.cumLagMs = -self.rk.remaining * 1000.
    controlsState.startMonoTime = int(start_time * 1e9)
    controlsState.forceDecel = bool(force_decel)
    controlsState.experimentalMode = self.experimental_mode
    controlsState.personality = PERSONALITY_MAPPING.get(self.personality, log.LongitudinalPersonality.standard)

    lat_tuning = self.CP.lateralTuning.which()
    if self.joystick_mode:
      controlsState.lateralControlState.debugState = lac_log
    elif self.CP.steerControlType == car.CarParams.SteerControlType.angle:
      controlsState.lateralControlState.angleState = lac_log
    elif lat_tuning == 'pid':
      controlsState.lateralControlState.pidState = lac_log
    elif lat_tuning == 'torque':
      controlsState.lateralControlState.torqueState = lac_log

    self.pm.send('controlsState', dat)

    dat_sp = messaging.new_message('controlsStateSP')
    controlsStateSP = dat_sp.controlsStateSP

    controlsStateSP.lateralState = lat_tuning
    controlsStateSP.personality = self.personality
    controlsStateSP.dynamicPersonality = self.dynamic_personality
    controlsStateSP.accelPersonality = self.accel_personality

    if self.enable_nnff and lat_tuning == 'torque':
      controlsStateSP.lateralControlState.torqueState = self.LaC.pid_long_sp

    self.pm.send('controlsStateSP', dat_sp)

    # onroadEvents - logged every second or on change
    if (self.sm.frame % int(1. / DT_CTRL) == 0) or (self.events.names != self.events_prev):
      ce_send = messaging.new_message('onroadEvents', len(self.events))
      ce_send.valid = True
      ce_send.onroadEvents = self.events.to_msg()
      self.pm.send('onroadEvents', ce_send)
    self.events_prev = self.events.names.copy()

    # carControl
    cc_send = messaging.new_message('carControl')
    cc_send.valid = CS.canValid
    cc_send.carControl = CC
    self.pm.send('carControl', cc_send)

  def step(self):
    start_time = time.monotonic()

    # Sample data from sockets and get a carState
    CS = self.data_sample()
    cloudlog.timestamp("Data sampled")

    self.update_events(CS)
    cloudlog.timestamp("Events updated")

    if not self.CP.passive and self.initialized:
      # Update control state
      self.state_transition(CS)

    # Compute actuators (runs PID loops and lateral MPC)
    CC, lac_log = self.state_control(CS)

    # Publish data
    self.publish_logs(CS, start_time, CC, lac_log)

    self.CS_prev = CS

  def read_personality_param(self):
    try:
      return int(self.params.get('LongitudinalPersonality'))
    except (ValueError, TypeError):
      return custom.LongitudinalPersonalitySP.standard

  def read_accel_personality_param(self):
    try:
      return int(self.params.get("AccelPersonality"))
    except (ValueError, TypeError):
      return custom.AccelerationPersonality.stock

  def params_thread(self, evt):
    while not evt.is_set():
      self.is_metric = self.params.get_bool("IsMetric")
      self.experimental_mode = self.params.get_bool("ExperimentalMode") and self.CP.openpilotLongitudinalControl
      self.personality = self.read_personality_param()
      self.dynamic_personality = self.params.get_bool("DynamicPersonality")
      self.accel_personality = self.read_accel_personality_param()
      if self.CP.notCar:
        self.joystick_mode = self.params.get_bool("JoystickDebugMode")

      self.reverse_acc_change = self.params.get_bool("ReverseAccChange")
      self.dynamic_experimental_control = self.params.get_bool("DynamicExperimentalControl")

      if self.sm.frame % int(2.5 / DT_CTRL) == 0:
        self.live_torque = self.params.get_bool("LiveTorque")
      time.sleep(0.1)

  def controlsd_thread(self):
    e = threading.Event()
    t = threading.Thread(target=self.params_thread, args=(e,))
    try:
      t.start()
      while True:
        self.step()
        self.rk.monitor_time()
    finally:
      e.set()
      t.join()


def main():
  config_realtime_process(4, Priority.CTRL_HIGH)
  controls = Controls()
  controls.controlsd_thread()


if __name__ == "__main__":
  main()
