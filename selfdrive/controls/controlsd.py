#!/usr/bin/env python3
import math
import json
import time
from numbers import Number

from cereal import car, log
import cereal.messaging as messaging
from openpilot.common.constants import CV
from openpilot.common.params import Params, UnknownKeyName
from openpilot.common.realtime import config_realtime_process, DT_CTRL, Priority, Ratekeeper
from openpilot.common.swaglog import cloudlog

from opendbc.car.car_helpers import interfaces
from opendbc.car.vehicle_model import VehicleModel
from openpilot.selfdrive.controls.lib.drive_helpers import clip_curvature
from openpilot.selfdrive.controls.lib.latcontrol import LatControl
from openpilot.selfdrive.controls.lib.latcontrol_pid import LatControlPID
from openpilot.selfdrive.controls.lib.latcontrol_angle import LatControlAngle, STEER_ANGLE_SATURATION_THRESHOLD
from openpilot.selfdrive.controls.lib.latcontrol_torque import LatControlTorque
from openpilot.selfdrive.controls.lib.longcontrol import LongControl
from openpilot.selfdrive.modeld.modeld import LAT_SMOOTH_SECONDS
from openpilot.selfdrive.locationd.helpers import PoseCalibrator, Pose

from openpilot.sunnypilot.selfdrive.controls.controlsd_ext import ControlsExt

# [AdriPilot] Modo 3 (COMMA+JETSON): estado del esquive de obstáculos
try:
  from openpilot.sicuem.adripilot.adripilot_obstacle_pulse import ObstaclePulseState, DEFAULT_MAX_ANGLE, DEFAULT_MAX_CURV
  _ADRIPILOT_OBSTACLE = True
except Exception:
  ObstaclePulseState = None
  DEFAULT_MAX_ANGLE, DEFAULT_MAX_CURV = 25.0, 0.030
  _ADRIPILOT_OBSTACLE = False

# Anti-flicker: cuando JetsonObstacleStatus pasa de activo a "" lo mantenemos
# publicado este tiempo para que la UI (~20 Hz) no pierda dodges muy breves.
OBSTACLE_STATUS_HOLD_S = 0.30

State = log.SelfdriveState.OpenpilotState
LaneChangeState = log.LaneChangeState
LaneChangeDirection = log.LaneChangeDirection

ACTUATOR_FIELDS = tuple(car.CarControl.Actuators.schema.fields.keys())


class Controls(ControlsExt):
  def __init__(self) -> None:
    self.params = Params()
    cloudlog.info("controlsd is waiting for CarParams")
    self.CP = messaging.log_from_bytes(self.params.get("CarParams", block=True), car.CarParams)
    cloudlog.info("controlsd got CarParams")

    # Initialize sunnypilot controlsd extension and base model state
    ControlsExt.__init__(self, self.CP, self.params)

    self.CI = interfaces[self.CP.carFingerprint](self.CP, self.CP_SP)

    self.sm = messaging.SubMaster(['liveDelay', 'liveParameters', 'liveTorqueParameters', 'modelV2', 'selfdriveState',
                                   'liveCalibration', 'livePose', 'longitudinalPlan', 'lateralManeuverPlan', 'carState', 'carOutput',
                                   'driverMonitoringState', 'onroadEvents', 'driverAssistance', 'liveDelay'] + self.sm_services_ext,
                                  poll='selfdriveState')
    self.pm = messaging.PubMaster(['carControl', 'controlsState'] + self.pm_services_ext)

    self.steer_limited_by_safety = False
    self.curvature = 0.0
    self.desired_curvature = 0.0

    self.pose_calibrator = PoseCalibrator()
    self.calibrated_pose: Pose | None = None

    self.LoC = LongControl(self.CP, self.CP_SP)
    self.VM = VehicleModel(self.CP)
    self.LaC: LatControl
    if self.CP.steerControlType == car.CarParams.SteerControlType.angle:
      self.LaC = LatControlAngle(self.CP, self.CP_SP, self.CI, DT_CTRL)
    elif self.CP.lateralTuning.which() == 'pid':
      self.LaC = LatControlPID(self.CP, self.CP_SP, self.CI, DT_CTRL)
    elif self.CP.lateralTuning.which() == 'torque':
      self.LaC = LatControlTorque(self.CP, self.CP_SP, self.CI, DT_CTRL)

    self.LaC = ControlsExt.initialize_lateral_control(self, self.LaC, self.CI, DT_CTRL)

    # [AdriPilot] limpiar cualquier pulso de dirección (cruceta MQTT) pendiente al iniciar
    try:
      from openpilot.sicuem.adripilot.adripilot_steering_pulse import clear_steering_pulse
      clear_steering_pulse()
    except Exception:
      pass

    # [AdriPilot] Modo 3 (COMMA+JETSON): estado del esquive y caché de config
    self._obstacle_pulse_state = ObstaclePulseState() if _ADRIPILOT_OBSTACLE else None
    self._last_obstacle_status = ""
    self._obstacle_status_hold_until = 0.0   # wall-clock hasta el que mantenemos el último activo
    self._obstacle_status_held_value = ""    # último status activo que estamos manteniendo
    self._obstacle_config_last_read = 0.0    # wall-clock; recachear cada 1s
    self._obstacle_max_angle = DEFAULT_MAX_ANGLE
    self._obstacle_max_curv = DEFAULT_MAX_CURV
    self._obstacle_apply_target = "curvature"  # "curvature" | "torque"

  def _refresh_obstacle_config(self, now: float) -> None:
    """Lee los params de configuración del esquive con cache de 1s. Siembra el default si falta."""
    if now - self._obstacle_config_last_read < 1.0:
      return
    self._obstacle_config_last_read = now
    for key, default, attr in (
      ("JetsonObstacleMaxAngle", DEFAULT_MAX_ANGLE, "_obstacle_max_angle"),
      ("JetsonObstacleMaxCurv", DEFAULT_MAX_CURV, "_obstacle_max_curv"),
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

  def update(self):
    self.sm.update(15)
    if self.sm.updated["liveCalibration"]:
      self.pose_calibrator.feed_live_calib(self.sm['liveCalibration'])
    if self.sm.updated["livePose"]:
      device_pose = Pose.from_live_pose(self.sm['livePose'])
      self.calibrated_pose = self.pose_calibrator.build_calibrated_pose(device_pose)

  def state_control(self):
    CS = self.sm['carState']

    # Update VehicleModel
    lp = self.sm['liveParameters']
    x = max(lp.stiffnessFactor, 0.1)
    sr = max(lp.steerRatio, 0.1)
    self.VM.update_params(x, sr)

    steer_angle_without_offset = math.radians(CS.steeringAngleDeg - lp.angleOffsetDeg)
    self.curvature = -self.VM.calc_curvature(steer_angle_without_offset, CS.vEgo, lp.roll)

    # Update Torque Params
    if self.CP.lateralTuning.which() == 'torque':
      torque_params = self.sm['liveTorqueParameters']
      if self.sm.all_checks(['liveTorqueParameters']) and torque_params.useParams:
        self.LaC.update_live_torque_params(torque_params.latAccelFactorFiltered, torque_params.latAccelOffsetFiltered,
                                           torque_params.frictionCoefficientFiltered)

        self.LaC.extension.update_limits()

      self.LaC.extension.update_model_v2(self.sm['modelV2'])

      self.LaC.extension.update_lateral_lag(self.lat_delay)

    long_plan = self.sm['longitudinalPlan']
    model_v2 = self.sm['modelV2']

    CC = car.CarControl.new_message()
    CC.enabled = self.sm['selfdriveState'].enabled

    # Check which actuators can be enabled
    standstill = abs(CS.vEgo) <= max(self.CP.minSteerSpeed, 0.3) or CS.standstill

    # Get which state to use for active lateral control
    _lat_active = self.get_lat_active(self.sm)

    CC.latActive = _lat_active and not CS.steerFaultTemporary and not CS.steerFaultPermanent and \
                   (not standstill or self.CP.steerAtStandstill)
    CC.longActive = CC.enabled and not any(e.overrideLongitudinal for e in self.sm['onroadEvents']) and \
                    (self.CP.openpilotLongitudinalControl or not self.CP_SP.pcmCruiseSpeed)

    actuators = CC.actuators
    actuators.longControlState = self.LoC.long_control_state

    # Enable blinkers while lane changing
    if model_v2.meta.laneChangeState != LaneChangeState.off:
      CC.leftBlinker = model_v2.meta.laneChangeDirection == LaneChangeDirection.left
      CC.rightBlinker = model_v2.meta.laneChangeDirection == LaneChangeDirection.right

    if not CC.latActive:
      self.LaC.reset()
    if not CC.longActive:
      self.LoC.reset()

    # accel PID loop
    pid_accel_limits = self.CI.get_pid_accel_limits(self.CP, self.CP_SP, CS.vEgo, CS.vCruise * CV.KPH_TO_MS)
    actuators.accel = float(self.LoC.update(CC.longActive, CS, long_plan.aTarget, long_plan.shouldStop, pid_accel_limits))

    # [AdriPilot] Brutebreak: frenado de emergencia brusco por comando MQTT.
    # Solo tiene efecto si CC.longActive (Comma controla longitudinal). Auto-clear con vEgo<0.5.
    try:
      if self.params.get_bool("brutebreak_active"):
        intensidad_frenado = -3.5
        try:
          intensidad_raw = self.params.get("brutebreak_intensidad")
          if intensidad_raw:
            intensidad = float(intensidad_raw.decode("utf-8") if isinstance(intensidad_raw, bytes) else intensidad_raw)
            if -10.0 <= intensidad <= -1.0:
              intensidad_frenado = intensidad
        except Exception:
          pass
        actuators.accel = max(intensidad_frenado, pid_accel_limits[0])
        if CS.vEgo < 0.5:
          self.params.put_bool("brutebreak_active", False)
    except Exception:
      pass  # hot-path: nunca propagar

    # Steering PID loop and lateral MPC
    # Reset desired curvature to current to avoid violating the limits on engage
    if self.sm.valid['lateralManeuverPlan']:
      new_desired_curvature = self.sm['lateralManeuverPlan'].desiredCurvature if CC.latActive else self.curvature
    else:
      new_desired_curvature = model_v2.action.desiredCurvature if CC.latActive else self.curvature
    self.desired_curvature, curvature_limited = clip_curvature(CS.vEgo, self.desired_curvature, new_desired_curvature, lp.roll)
    lat_delay = self.sm["liveDelay"].lateralDelay + LAT_SMOOTH_SECONDS

    actuators.curvature = self.desired_curvature
    steer, steeringAngleDeg, lac_log = self.LaC.update(CC.latActive, CS, self.VM, lp,
                                                       self.steer_limited_by_safety, self.desired_curvature,
                                                       self.calibrated_pose, curvature_limited, lat_delay)
    actuators.torque = float(steer)
    actuators.steeringAngleDeg = float(steeringAngleDeg)

    # ════════════════════════════════════════════════════════════════
    # [AdriPilot] SELECTOR DE FUENTE DE TORQUE LATERAL (param SteerTorqueMode)
    #   0=Comma (sin tocar)  1=Jetson (JetsonTorque)  2=TEST MAX (-1.0)  3=Comma+Jetson (esquive)
    # NOTA: en este sunnypilot el campo es actuators.torque (antes actuators.steer).
    # ════════════════════════════════════════════════════════════════
    steer_mode = 0
    if CC.latActive:
      try:
        self.params.put_nonblocking("CommaSteerTorque", f"{float(actuators.torque):.4f}")
      except Exception:
        pass
      try:
        mode_raw = self.params.get("SteerTorqueMode")
      except UnknownKeyName:
        cloudlog.error("SteerTorqueMode no registrado en params_keys.h.")
        mode_raw = None
      try:
        steer_mode = int(mode_raw) if mode_raw else 0
      except (ValueError, TypeError):
        steer_mode = 0

      if steer_mode == 1:
        # FUENTE JETSON: torque ya normalizado [-1,1] que publica zmq_client.py en JetsonTorque.
        # FAIL-SAFE: si no se puede leer -> 0.0 (volante sin fuerza), nunca dejar pasar Comma en silencio.
        try:
          jt = float(self.params.get("JetsonTorque") or 0.0)
        except (UnknownKeyName, ValueError, TypeError):
          jt = 0.0
        actuators.torque = jt
      elif steer_mode == 2:
        actuators.torque = -1.0  # TEST MAX (banco), tras confirmación en la UI
      elif steer_mode == 3:
        pass  # COMMA+JETSON: el torque base lo deja Comma; abajo se aplican los offsets de esquive

      try:
        self.params.put_nonblocking("AppliedSteerTorque", f"{float(actuators.torque):.4f}")
      except UnknownKeyName:
        pass

    # [AdriPilot] Pulso temporal de dirección (cruceta MQTT): +/- ángulo y curvatura mientras está activo
    try:
      from openpilot.sicuem.adripilot.adripilot_steering_pulse import get_steering_pulse, adripilot_steering_pulse_angle
      pulse_start, original_direction, is_active, phase, effective_direction = get_steering_pulse()
      if is_active and effective_direction in ("right", "left") and CC.latActive:
        if effective_direction == "right":
          actuators.steeringAngleDeg = float(actuators.steeringAngleDeg) + adripilot_steering_pulse_angle
          self.desired_curvature += 0.008
        else:
          actuators.steeringAngleDeg = float(actuators.steeringAngleDeg) - adripilot_steering_pulse_angle
          self.desired_curvature -= 0.008
        actuators.curvature = self.desired_curvature
    except ImportError:
      pass
    except Exception:
      pass

    # [AdriPilot] MODO 3 (COMMA+JETSON): offsets de esquive por obstáculo (override absoluto)
    try:
      if CC.latActive and steer_mode == 3 and self._obstacle_pulse_state is not None:
        now_pulse = time.time()
        self._refresh_obstacle_config(now_pulse)
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
        bsm_blocked = status in ("BSM_BLOCKED_LEFT", "BSM_BLOCKED_RIGHT")
        if self._obstacle_pulse_state.active and not bsm_blocked:
          if self._obstacle_apply_target == "torque":
            intensity = self._obstacle_pulse_state.intensity
            if math.isnan(intensity):
              intensity = 0.0
            actuators.torque = max(-1.0, min(1.0, intensity))
          else:
            actuators.steeringAngleDeg = angle_tgt
            self.desired_curvature = curv_tgt
            actuators.curvature = self.desired_curvature

        if status in ("DODGING_LEFT", "DODGING_RIGHT", "DODGING_HOLD", "BSM_BLOCKED_LEFT", "BSM_BLOCKED_RIGHT"):
          self._obstacle_status_held_value = status
          self._obstacle_status_hold_until = now_pulse + OBSTACLE_STATUS_HOLD_S
          published = status
        elif self._obstacle_status_held_value and now_pulse < self._obstacle_status_hold_until:
          published = self._obstacle_status_held_value
        else:
          self._obstacle_status_held_value = ""
          published = status

        if published != self._last_obstacle_status:
          try:
            self.params.put_nonblocking("JetsonObstacleStatus", published)
            self.params.put_nonblocking("JetsonObstacleStatusMqttPayload",
                                        json.dumps({"status": published, "ts": now_pulse, "source": "comma"}))
          except UnknownKeyName:
            pass
          self._last_obstacle_status = published

      elif self._obstacle_pulse_state is not None and \
           (self._obstacle_pulse_state.active or self._obstacle_status_held_value or self._last_obstacle_status):
        self._obstacle_pulse_state._reset()
        self._obstacle_status_held_value = ""
        self._obstacle_status_hold_until = 0.0
        if self._last_obstacle_status:
          try:
            self.params.put_nonblocking("JetsonObstacleStatus", "")
            self.params.put_nonblocking("JetsonObstacleStatusMqttPayload",
                                        json.dumps({"status": "", "ts": time.time(), "source": "comma"}))
          except UnknownKeyName:
            pass
          self._last_obstacle_status = ""
    except Exception as e:
      cloudlog.error(f"controlsd: excepcion inesperada en bloque modo 3: {e}")

    # Ensure no NaNs/Infs
    for p in ACTUATOR_FIELDS:
      attr = getattr(actuators, p)
      if not isinstance(attr, Number):
        continue

      if not math.isfinite(attr):
        cloudlog.error(f"actuators.{p} not finite {actuators.to_dict()}")
        setattr(actuators, p, 0.0)

    return CC, lac_log

  def publish(self, CC, lac_log):
    CS = self.sm['carState']

    # Orientation and angle rates can be useful for carcontroller
    # Only calibrated (car) frame is relevant for the carcontroller
    CC.currentCurvature = self.curvature
    if self.calibrated_pose is not None:
      CC.orientationNED = self.calibrated_pose.orientation.xyz.tolist()
      CC.angularVelocity = self.calibrated_pose.angular_velocity.xyz.tolist()

    CC.cruiseControl.override = CC.enabled and not CC.longActive and (self.CP.openpilotLongitudinalControl or not self.CP_SP.pcmCruiseSpeed)
    CC.cruiseControl.cancel = CS.cruiseState.enabled and (not CC.enabled or not self.CP.pcmCruise)
    CC.cruiseControl.resume = CC.enabled and CS.cruiseState.standstill and not self.sm['longitudinalPlan'].shouldStop

    hudControl = CC.hudControl
    hudControl.setSpeed = float(CS.vCruiseCluster * CV.KPH_TO_MS)
    hudControl.speedVisible = CC.enabled
    hudControl.lanesVisible = CC.enabled
    hudControl.leadVisible = self.sm['longitudinalPlan'].hasLead
    hudControl.leadDistanceBars = self.sm['selfdriveState'].personality.raw + 1
    hudControl.visualAlert = self.sm['selfdriveState'].alertHudVisual

    hudControl.rightLaneVisible = True
    hudControl.leftLaneVisible = True
    if self.sm.valid['driverAssistance']:
      hudControl.leftLaneDepart = self.sm['driverAssistance'].leftLaneDeparture
      hudControl.rightLaneDepart = self.sm['driverAssistance'].rightLaneDeparture

    if self.get_lat_active(self.sm):
      CO = self.sm['carOutput']
      if self.CP.steerControlType == car.CarParams.SteerControlType.angle:
        self.steer_limited_by_safety = abs(CC.actuators.steeringAngleDeg - CO.actuatorsOutput.steeringAngleDeg) > \
                                              STEER_ANGLE_SATURATION_THRESHOLD
      else:
        self.steer_limited_by_safety = abs(CC.actuators.torque - CO.actuatorsOutput.torque) > 1e-2

    # TODO: both controlsState and carControl valids should be set by
    #       sm.all_checks(), but this creates a circular dependency

    # controlsState
    dat = messaging.new_message('controlsState')
    dat.valid = CS.canValid
    cs = dat.controlsState

    cs.curvature = self.curvature
    cs.longitudinalPlanMonoTime = self.sm.logMonoTime['longitudinalPlan']
    cs.lateralPlanMonoTime = self.sm.logMonoTime['modelV2']
    cs.desiredCurvature = self.desired_curvature
    cs.longControlState = self.LoC.long_control_state
    cs.upAccelCmd = float(self.LoC.pid.p)
    cs.uiAccelCmd = float(self.LoC.pid.i)
    cs.ufAccelCmd = float(self.LoC.pid.f)
    cs.forceDecel = bool((self.sm['driverMonitoringState'].alertLevel == log.DriverMonitoringState.AlertLevel.three) or
                         (self.sm['selfdriveState'].state == State.softDisabling))

    lat_tuning = self.CP.lateralTuning.which()
    if self.CP.steerControlType == car.CarParams.SteerControlType.angle:
      cs.lateralControlState.angleState = lac_log
    elif lat_tuning == 'pid':
      cs.lateralControlState.pidState = lac_log
    elif lat_tuning == 'torque':
      cs.lateralControlState.torqueState = lac_log

    self.pm.send('controlsState', dat)

    # carControl
    cc_send = messaging.new_message('carControl')
    cc_send.valid = CS.canValid
    cc_send.carControl = CC
    self.pm.send('carControl', cc_send)

  def run(self):
    rk = Ratekeeper(100, print_delay_threshold=None)
    while True:
      self.update()
      CC, lac_log = self.state_control()
      self.publish(CC, lac_log)
      self.get_params_sp(self.sm)
      self.run_ext(self.sm, self.pm)
      rk.monitor_time()


def main():
  config_realtime_process(4, Priority.CTRL_HIGH)
  controls = Controls()
  controls.run()


if __name__ == "__main__":
  main()
