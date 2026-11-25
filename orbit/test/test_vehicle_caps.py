"""Bloque `vehicle` de los caps, sacado de carParams por el GateMonitor (C-24)."""
import json
from types import SimpleNamespace

from openpilot.orbit.command_gates import GateMonitor
from openpilot.orbit.command_router import CommandRouter


class _SubMaster:
  def __init__(self, datos):
    self.datos = datos
    self.alive = dict.fromkeys(datos, True)
    self.valid = dict.fromkeys(datos, True)
    self.seen = dict.fromkeys(datos, True)

  def __getitem__(self, k):
    return self.datos[k]

  def update(self, timeout=0):
    pass


def _car_params(**kw):
  base = dict(brand="hyundai", carFingerprint="HYUNDAI_IONIQ_5", dashcamOnly=False, passive=False,
              openpilotLongitudinalControl=True, steerControlType="angle", enableBsm=True,
              radarUnavailable=True, pcmCruise=False, carVin="KMHXX00XXXX000000")
  base.update(kw)
  return SimpleNamespace(**base)


def _caps(gm):
  r = CommandRouter("0123456789abcdef", gates=gm, params=None)
  return r.capabilities_payload()


def test_vehicle_exacto_con_carparams():
  gm = GateMonitor(sm=_SubMaster({"carParams": _car_params()}))
  gm.update(0)
  esperado = {"long_op": True, "steer_type": "angle", "bsm": True, "radarless": True, "pcm_cruise": False}
  assert gm.vehicle == esperado
  caps = _caps(gm)
  assert caps["vehicle"] == esperado
  assert "vin" not in json.dumps(caps).lower()
  assert "KMHXX" not in json.dumps(caps)


def test_steer_type_raro_es_unknown_y_enum_capnp():
  from cereal import car
  gm = GateMonitor(sm=_SubMaster({"carParams": _car_params(steerControlType="raro")}))
  gm.update(0)
  assert gm.vehicle["steer_type"] == "unknown"
  cp = car.CarParams.new_message(steerControlType="torque")
  gm = GateMonitor(sm=_SubMaster({"carParams": cp}))
  gm.update(0)
  assert gm.vehicle["steer_type"] == "torque"


def test_sin_carparams_no_hay_vehicle():
  gm = GateMonitor(sm=_SubMaster({"deviceState": SimpleNamespace(started=False)}))
  gm.update(0)
  assert gm.vehicle is None
  assert "vehicle" not in _caps(gm)
  assert "vehicle" not in CommandRouter("0123456789abcdef", gates=None).capabilities_payload()
