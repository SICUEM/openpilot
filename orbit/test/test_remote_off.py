"""OrbitRemoteOff en los caminos MQTT de MQTTComandos y MQTTEnvioGeneral (C-33.3, C-33.9).

El interruptor se lee del Param (doble en memoria) en cada decision, sin cache. Los casos
del router puro estan en test_mando_local.py; aqui van los caminos 1-9 tal como entran
por on_message, los caps y el caso "sin telemetria".
"""
import json

import pytest

from openpilot.orbit import config_v2 as cfg2
from openpilot.orbit import mando_local, mqtt_comandos
from openpilot.orbit.command_spec import TOPIC_CAPS, Phase, ahora_epoch_ms
from openpilot.orbit.mando_local import get_mando_local
from openpilot.orbit.mqtt_envio_general import MQTTEnvioGeneral
from openpilot.orbit.test.test_config_y_privacidad_loop import CamaraFalsa, ParamsFalsos, _envio, _sobre
from openpilot.orbit.test.test_mando_v1_por_router import (DONGLE, V1, V2, _acks, _comandos, _entregar,
                                                           _ParamsFalsos)


@pytest.fixture(autouse=True)
def _limpio(monkeypatch):
  monkeypatch.setattr(mando_local, "_singleton", None)
  monkeypatch.setattr(mqtt_comandos, "get_key_pair", lambda: (None, None, None))
  cfg2.get_bus().tomar()
  yield
  cfg2.get_bus().tomar()


def _apagado(**valores):
  return _comandos(params=_ParamsFalsos({"OrbitRemoteOff": True, **valores}))


_N = [0]


def _sobre_v2(verb="lane_change", args=None):
  _N[0] += 1
  n = _N
  return json.dumps({"v": 2, "id": f"rof-mqtt-{n[0]}", "seq": n[0], "verb": verb,
                     "args": {"direction": "left"} if args is None else args,
                     "ts_ms": ahora_epoch_ms(), "ttl_ms": 3000, "mode": "maniobra", "actor": {}})


def _caps(c):
  assert c.maybe_publish_caps(forzar=True)
  return json.loads([p for t, p, *_ in c.mqttc.publicados if t == TOPIC_CAPS.format(DONGLE)][-1])


def _registro():
  return [(f["o"], f["v"], f["f"], f["r"]) for f in get_mando_local().filas()]


# ---------------------------------------------------------------- caminos 1-3 (router)

def test_lane_change_v2_rechazado_y_ningun_param_escrito():
  c = _apagado()
  antes = dict(c.params.valores)
  _entregar(c, V2, _sobre_v2())
  assert (Phase.REJECTED, "REMOTE_OFF") in _acks(c)
  assert c.params.valores == antes
  assert ("v2", "lane_change", "rejected", "REMOTE_OFF") in _registro()


def test_disarm_all_v2_se_aplica():
  c = _apagado()
  _entregar(c, V2, _sobre_v2("disarm_all", {}))
  assert (Phase.APPLIED, "OK") in _acks(c)


def test_v1_left_remote_off():
  c = _apagado()
  _entregar(c, f"{V1}/left", '{"ForceLaneChangeLeft": true}')
  assert (Phase.REJECTED, "REMOTE_OFF") in _acks(c)
  assert c.params.valores.get("ForceLaneChangeLeft") is not True


# ---------------------------------------------------------------- camino 4: cfg/desired

def test_cfg_desired_retenido_y_aplicado_al_quitar_el_interruptor(tmp_path):
  c = _apagado()
  _entregar(c, cfg2.TOPIC_CFG_DESIRED.format(DONGLE), _sobre(version=4, telemetry_profile="ahorro"))
  assert ("cfg", "cfg", "held", "REMOTE_OFF") in _registro()

  e = _envio(tmp_path, params=ParamsFalsos({"OrbitRemoteOff": True}))
  e._mantener_config(1000.0)
  assert cfg2.get_bus().estado()["pendiente"] is True
  assert "OrbitTelemetryProfile" not in e.params.valores

  e.params.valores["OrbitRemoteOff"] = False
  e._mantener_config(2000.0)
  assert cfg2.get_bus().estado()["pendiente"] is False
  assert e.params.valores["OrbitTelemetryProfile"] == "ahorro"


# ---------------------------------------------------------------- camino 5: roundabout

def test_roundabout_1_ignorado_y_0_se_escribe():
  c = _apagado()
  topic = cfg2.TOPIC_DEV_ROUNDABOUT.format(DONGLE)
  _entregar(c, topic, "1")
  assert "OrbitDevRoundabout" not in c.params.valores
  assert ("dev", "roundabout", "ignored", "REMOTE_OFF") in _registro()
  _entregar(c, topic, "0")
  assert c.params.valores["OrbitDevRoundabout"] is False


# ---------------------------------------------------------------- camino 6: camera_config

def test_camera_config_solo_pasa_el_apagado():
  c = _apagado()
  cam = CamaraFalsa()
  c.camera_sender = cam
  _entregar(c, f"{V1}/camera_config", json.dumps({"image_sending_enabled": True}))
  assert cam.aplicados == []
  _entregar(c, f"{V1}/camera_config", json.dumps({"image_sending_enabled": False, "send_frequency_seconds": 1}))
  assert cam.aplicados == [{"image_sending_enabled": False}]
  _entregar(c, f"{V1}/camera_config", "{roto")
  assert len(get_mando_local().filas()) == 2


def test_camera_config_sin_interruptor_se_aplica_entero():
  c = _comandos(params=_ParamsFalsos())
  cam = CamaraFalsa()
  c.camera_sender = cam
  _entregar(c, f"{V1}/camera_config", json.dumps({"image_sending_enabled": True, "send_frequency_seconds": 5}))
  assert cam.aplicados == [{"image_sending_enabled": True, "send_frequency_seconds": 5}]
  assert _registro() == [("cam", "cam", "applied", "")]


def test_camera_config_registro_veraz_sin_interruptor():
  c = _comandos(params=_ParamsFalsos())
  cam = CamaraFalsa()
  c.camera_sender = cam
  # No cambia nada (ya estaba apagado): ignored, no applied.
  _entregar(c, f"{V1}/camera_config", json.dumps({"image_sending_enabled": False}))
  assert _registro() == [("cam", "cam", "ignored", "")]
  # JSON roto: vuelve a pasar por el handler, que lo ignora y lo dice.
  llamadas = []
  original = c.handle_camera_config
  c.handle_camera_config = lambda p: llamadas.append(p) or original(p)
  _entregar(c, f"{V1}/camera_config", "{roto")
  assert llamadas == ["{roto"]
  assert get_mando_local().filas()[0]["n"] == 2   # otra fila ignored, deduplicada
  # Sin CameraSender tampoco se aplica nada.
  c.camera_sender = None
  _entregar(c, f"{V1}/camera_config", json.dumps({"image_sending_enabled": True}))
  assert _registro() == [("cam", "cam", "ignored", "")]


# ---------------------------------------------------------------- camino 7: speed_increment

def test_speed_increment_intacto():
  c = _apagado(orbit_speed_increment=2.0)
  _entregar(c, f"{V1}/speed_increment", "5")
  assert c.params.valores["orbit_speed_increment"] == 2.0
  assert ("paso", "speed_increment", "ignored", "REMOTE_OFF") in _registro()


# ---------------------------------------------------------------- caminos 8-9: identidad

def test_enroll_ack_y_unlink_ack_se_procesan():
  c = _apagado(OrbitUnlinkRequest=True, OrbitUnlinkNonce="n")
  _entregar(c, f"{V1}/enroll_ack", json.dumps({"claimed": True, "user_id": 7, "user_name": "Ana"}), retain=True)
  assert c.params.valores["OrbitClaimed"] is True
  _entregar(c, f"{V1}/unlink_ack", json.dumps({"ok": True}))
  assert "OrbitUnlinkRequest" not in c.params.valores
  assert json.loads(c.params.valores["OrbitUnlinkResult"])["ok"] is True


# ---------------------------------------------------------------- sin telemetria

def test_sin_telemetria_el_router_sigue_rechazando():
  c = _comandos(params=_ParamsFalsos())
  e = MQTTEnvioGeneral.__new__(MQTTEnvioGeneral)
  e.params = c.params
  e.comandos_mqtt = c
  e.conectado = False
  e.dongle_valido = True
  e._camera_pendiente = False
  e.mqttc = object()
  for m in ("_maybe_reload_broker", "_maybe_reload_canales", "_maybe_announce_enroll", "_maybe_send_unlink"):
    setattr(e, m, lambda: None)
  volcados = []
  c.volcar_registro = lambda: volcados.append(1)
  e._ciclo_v1()                              # sale por "sin conexion"
  assert volcados == [1]                     # el volcado va antes de cualquier return

  c.params.valores["OrbitRemoteOff"] = True
  _entregar(c, V2, _sobre_v2())
  assert (Phase.REJECTED, "REMOTE_OFF") in _acks(c)


# ---------------------------------------------------------------- caps, bookmark y registro

def test_caps_incluye_remote_off_y_fw_commit():
  c = _comandos(params=_ParamsFalsos())
  c._fw_commit = "abcdef123456"
  d = _caps(c)
  assert d["remote_off"] is False and d["fw_commit"] == "abcdef123456"
  c.params.valores["OrbitRemoteOff"] = True
  assert _caps(c)["remote_off"] is True
  c._fw_commit = ""
  assert "fw_commit" not in _caps(c)


def test_bookmark_registrado_sin_efectos():
  c = _comandos(params=_ParamsFalsos())
  assert "bookmark" in c.router.registered_verbs()
  antes = dict(c.params.valores)
  assert c._h_bookmark(None) is None
  assert c.params.valores == antes


def test_volcar_registro_escribe_el_param():
  c = _apagado()
  _entregar(c, V2, _sobre_v2())
  c.volcar_registro()
  filas = json.loads(c.params.valores["OrbitRemoteLog"])
  assert filas[0]["v"] == "lane_change" and filas[0]["r"] == "REMOTE_OFF"
