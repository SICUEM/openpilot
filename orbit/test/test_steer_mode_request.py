"""steer_mode_request: la app PIDE un modo de volante y una persona lo ACEPTA en el comma.

El broker es abierto, asi que por MQTT nunca sube la autoridad del volante: 1-3 solo dejan
una peticion en OrbitSteerModeRequest, y la unica forma de aplicarla es Aceptar en la
pantalla (orbit_peticion_modo), por el mismo camino que el selector local. El 0 BAJA
autoridad y se aplica al momento. Se recorre la cadena real: router -> handler -> Params ->
logica de la pantalla -> OrbitCmdResult -> router -> ACK.
"""
import json

import pytest

from openpilot.common.params import Params
from openpilot.orbit.command_router import CommandRouter
from openpilot.orbit.command_spec import Mode, Phase, ahora_epoch_ms, ahora_mono, get_spec, validar_args
from openpilot.orbit.mqtt_comandos import MQTTComandos
from openpilot.orbit.test.test_command_router_v2 import _GatesFalsos, _store
from openpilot.selfdrive.ui.widgets import orbit_mando
from openpilot.selfdrive.ui.widgets import orbit_peticion_modo as pm

DONGLE = "0123456789abcdef"
TOPIC = f"orbit/v2/cmd/{DONGLE}"


class _Comandos:
  """Lo minimo de MQTTComandos que usa el handler."""
  def __init__(self, params):
    self.params = params


@pytest.fixture
def entorno():
  # OpenpilotPrefix nuevo por test (conftest): el Params cacheado de orbit_mando apuntaria al viejo.
  orbit_mando._ParamsHolder._p = None
  pm._por_escribir.clear()
  params = Params()
  pub = []
  r = CommandRouter(DONGLE, gates=_GatesFalsos(), store=_store(Mode.OBSERVER),
                    publish=lambda t, p, q, ret: pub.append(json.loads(p)))
  c = _Comandos(params)
  r.register_handler("steer_mode_request", lambda cmd: MQTTComandos._h_steer_mode_request(c, cmd))
  yield r, pub, params
  orbit_mando._ParamsHolder._p = None


def _pide(r, cid, mode, apply_target=None, seq=None):
  args = {"mode": mode} if apply_target is None else {"mode": mode, "apply_target": apply_target}
  r.handle_payload(TOPIC, json.dumps({
    "v": 2, "id": cid, "seq": seq or int(ahora_mono() * 1000), "verb": "steer_mode_request", "args": args,
    "ts_ms": ahora_epoch_ms(), "mono_ms": 1, "ttl_ms": 30_000, "mode": "observador",
    "actor": {"user_id": 7, "via": "app"},
  }))
  r.drenar()


def _fases(pub, cid):
  return [p["phase"] for p in pub if p["id"] == cid]


def _ultimo(pub, cid):
  return [p for p in pub if p["id"] == cid][-1]


def _router_lee_resultado(r):
  dato = r._consumir_resultado()
  assert dato is not None, "la pantalla no escribio OrbitCmdResult"
  r._cerrar_con_resultado(dato)


def test_spec_del_verbo():
  s = get_spec("steer_mode_request")
  assert s.mode_min == Mode.OBSERVER and int(s.gates) == 0 and not s.requiere_armado_banco
  assert s.ttl_ms == 30_000 and s.cierra_consumidor and s.confirma_en_pantalla and not s.arma_actuador
  assert s.limits["apply_target_obligatorio_en"] == (3,)
  for ok in ({"mode": 0}, {"mode": 3, "apply_target": "torque"}, {"mode": 1, "apply_target": "curvature"}):
    assert validar_args(s, ok)[0] is None, ok
  assert validar_args(s, {"mode": 4})[0] == "RANGE"
  assert validar_args(s, {"mode": -1})[0] == "RANGE"
  assert validar_args(s, {"mode": True})[0] == "TYPE"
  assert validar_args(s, {"mode": 3, "apply_target": "volante"})[0] == "RANGE"
  assert validar_args(s, {})[0] is not None


def test_mode_3_sin_apply_target_se_rechaza(entorno):
  r, pub, params = entorno
  _pide(r, "m3", 3)
  assert _ultimo(pub, "m3")["phase"] == Phase.REJECTED and _ultimo(pub, "m3")["reason"] == "RANGE"
  assert params.get("OrbitSteerModeRequest") is None


def test_mode_0_aplica_al_momento_y_cierra_applied(entorno):
  r, pub, params = entorno
  params.put("SteerTorqueMode", 1, True)
  params.put_bool("OrbitSteerModeLocal", True, True)
  _pide(r, "m1", 1)
  _pide(r, "m0", 0)
  assert params.get("SteerTorqueMode", return_default=True) == 0 and not params.get_bool("OrbitSteerModeLocal")
  assert _ultimo(pub, "m0")["phase"] == Phase.APPLIED
  assert Phase.EXECUTING not in _fases(pub, "m0")
  # la peticion pendiente se retira
  assert params.get("OrbitSteerModeRequest") is None
  assert _ultimo(pub, "m1")["phase"] == Phase.SUPERSEDED
  assert not r._pendientes


def test_mode_1_escribe_la_peticion_sin_tocar_el_volante(entorno):
  r, pub, params = entorno
  _pide(r, "m1", 1)
  assert params.get("SteerTorqueMode", return_default=True) == 0 and not params.get_bool("OrbitSteerModeLocal")
  pet = json.loads(params.get("OrbitSteerModeRequest"))
  assert pet["v"] == 1 and pet["id"] == "m1" and pet["mode"] == 1 and pet["apply_target"] is None
  assert 25 < pet["deadline_mono"] - ahora_mono() <= 30
  assert _fases(pub, "m1")[-1] == Phase.ACCEPTED and Phase.EXECUTING not in _fases(pub, "m1")
  assert pm.texto(pm.tick(params)) == "La app pide modo JETSON"


def test_aceptar_aplica_el_modo_y_cierra_applied(entorno):
  r, pub, params = entorno
  _pide(r, "m3", 3, "torque")
  assert pm.texto(pm.tick(params)) == "La app pide modo COMMA+JETSON (TORQUE)"
  assert pm.aceptar(params, engaged=False)
  assert params.get("SteerTorqueMode", return_default=True) == 3 and params.get("JetsonObstacleApplyTarget") == "torque"
  assert params.get("OrbitSteerModeRequest") is None
  _router_lee_resultado(r)
  assert _ultimo(pub, "m3")["phase"] == Phase.APPLIED


def test_aceptar_un_modo_de_override_da_la_autorizacion_presencial(entorno):
  r, _, params = entorno
  _pide(r, "m2", 2)
  assert pm.aceptar(params, engaged=False)
  assert params.get("SteerTorqueMode", return_default=True) == 2 and params.get_bool("OrbitSteerModeLocal")
  assert not params.get_bool("OrbitBenchArmed")


def test_aceptar_con_openpilot_enganchado_no_aplica_nada(entorno):
  r, pub, params = entorno
  _pide(r, "m1", 1)
  assert not pm.aceptar(params, engaged=True)
  assert params.get("SteerTorqueMode", return_default=True) == 0 and not params.get_bool("OrbitSteerModeLocal")
  assert params.get("OrbitSteerModeRequest") is not None and params.get("OrbitCmdResult") is None
  assert _fases(pub, "m1")[-1] == Phase.ACCEPTED


def test_rechazar_cierra_rejected(entorno):
  r, pub, params = entorno
  _pide(r, "m1", 1)
  assert pm.rechazar(params)
  assert params.get("SteerTorqueMode", return_default=True) == 0 and params.get("OrbitSteerModeRequest") is None
  _router_lee_resultado(r)
  ack = _ultimo(pub, "m1")
  assert (ack["phase"], ack["reason"], ack["detail"]) == (Phase.REJECTED, "MODE", "rechazado en el comma")


def test_peticion_caducada_no_se_puede_aceptar(entorno):
  r, pub, params = entorno
  _pide(r, "m1", 1)
  tarde = ahora_mono() + 31
  assert not pm.aceptar(params, engaged=False, ahora=tarde)
  assert params.get("SteerTorqueMode", return_default=True) == 0 and params.get("OrbitSteerModeRequest") is None
  _router_lee_resultado(r)
  assert _ultimo(pub, "m1")["phase"] == Phase.EXPIRED


def test_sin_pantalla_el_router_la_cierra_expired_y_no_no_result(entorno):
  r, pub, params = entorno
  _pide(r, "m1", 1)
  clave = next(iter(r._pendientes))
  r._pendientes[clave] = (r._pendientes[clave][0], ahora_mono() - 1)
  r._caducar_pendientes()
  assert _ultimo(pub, "m1")["phase"] == Phase.EXPIRED


def test_una_nueva_sustituye_a_la_anterior(entorno):
  r, pub, params = entorno
  _pide(r, "a", 1)
  _pide(r, "b", 2)
  assert _ultimo(pub, "a")["phase"] == Phase.SUPERSEDED
  assert json.loads(params.get("OrbitSteerModeRequest"))["id"] == "b"
  assert list(r._pendientes) == ["b"]
  assert pm.aceptar(params, engaged=False)
  assert params.get("SteerTorqueMode", return_default=True) == 2
  _router_lee_resultado(r)
  assert _ultimo(pub, "b")["phase"] == Phase.APPLIED


def test_el_resultado_espera_si_el_hueco_esta_ocupado(entorno):
  r, pub, params = entorno
  _pide(r, "m1", 1)
  params.put("OrbitCmdResult", '{"verb":"cruise_delta"}', True)
  assert pm.rechazar(params)
  assert json.loads(params.get("OrbitCmdResult"))["verb"] == "cruise_delta"   # no se pisa
  params.remove("OrbitCmdResult")
  pm.tick(params)
  assert json.loads(params.get("OrbitCmdResult"))["id"] == "m1"


def test_peticion_basura_no_se_pinta(entorno):
  _, _, params = entorno
  for crudo in ("{", '{"v":1,"id":"x","mode":0,"deadline_mono":1e12}',
                '{"v":1,"id":"x","mode":3,"apply_target":null,"deadline_mono":1e12}'):
    params.put("OrbitSteerModeRequest", crudo, True)
    assert pm.tick(params) is None and params.get("OrbitSteerModeRequest") is None
