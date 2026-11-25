"""Interruptor local OrbitRemoteOff en el router y registro de ordenes remotas (C-33).

Los caminos MQTT 4-7 y los caps de MQTTComandos van en test_remote_off.py.
"""
import ast
import json
import re
from pathlib import Path

import pytest

from openpilot.orbit import mando_local
from openpilot.orbit.command_router import CommandRouter
from openpilot.orbit.command_spec import Mode, Phase, ahora_epoch_ms
from openpilot.orbit.command_state import PARAM_BENCH_ARMED, PARAM_DISARM_ALL, PARAM_MODE, CommandStateStore
from openpilot.orbit.mando_local import MandoLocal, remoto_apagado

DONGLE = "0123456789abcdef"
TOPIC = f"orbit/v2/cmd/{DONGLE}"
RAIZ = Path(__file__).resolve().parents[2]


class _Params:
  def __init__(self, valores=None):
    self.valores = dict(valores or {})
    self.escritos = []

  def get(self, key, *a, **k):
    return self.valores.get(key)

  def get_bool(self, key, *a, **k):
    return bool(self.valores.get(key, False))

  def put(self, key, value, *a, **k):
    self.escritos.append(key)
    self.valores[key] = value

  def put_bool(self, key, value, *a, **k):
    self.put(key, bool(value))

  def remove(self, key):
    self.valores.pop(key, None)


class _ParamsQueLanza:
  def get_bool(self, *a, **k):
    raise RuntimeError("disco roto")


class _Gates:
  clock_synced = True
  brand = "ford"
  onroad = True

  def note_link(self, cuando_mono=None):
    pass

  def evaluate(self, spec, args=None):
    return True, []


def _router(params):
  st = CommandStateStore(params=_Params({PARAM_MODE: int(Mode.MANEUVER), PARAM_BENCH_ARMED: False,
                                         PARAM_DISARM_ALL: False}))
  st.refresh_params(forzar=True)
  pub, ej = [], []
  r = CommandRouter(DONGLE, gates=_Gates(), store=st, params=params,
                    publish=lambda t, p, q, ret: pub.append(json.loads(p)))
  for v in ("lane_change", "disarm_all"):
    r.register_handler(v, lambda cmd: ej.append(cmd.verb))
  return r, pub, ej


_N = [0]


def _sobre(verb="lane_change"):
  _N[0] += 1
  return json.dumps({"v": 2, "id": f"rof-{_N[0]}", "seq": _N[0], "verb": verb,
                     "args": {"direction": "left"} if verb == "lane_change" else {},
                     "ts_ms": ahora_epoch_ms(), "ttl_ms": 3000, "mode": "maniobra", "actor": {}})


def _terminal(pub, cmd_id):
  return [(p["phase"], p["reason"]) for p in pub if p["id"] == cmd_id and p["phase"] not in ("received", "accepted",
                                                                                           "executing")]


@pytest.fixture(autouse=True)
def _registro_limpio(monkeypatch):
  monkeypatch.setattr(mando_local, "_singleton", None)


# ---------------------------------------------------------------- interruptor

def test_remoto_apagado_falla_cerrado():
  assert remoto_apagado(_ParamsQueLanza()) is True
  assert remoto_apagado(None) is True
  assert remoto_apagado(_Params()) is False
  assert remoto_apagado(_Params({"OrbitRemoteOff": True})) is True


def test_params_reales_conocen_las_claves():
  from openpilot.common.params import Params
  p = Params()
  p.get_bool("OrbitRemoteOff")
  p.get("OrbitRemoteLog")


def test_lane_change_con_interruptor_rechaza_remote_off():
  params = _Params({"OrbitRemoteOff": True})
  r, pub, ej = _router(params)
  res = r.handle_payload(TOPIC, _sobre())
  assert not res.aceptado and res.reason == "REMOTE_OFF"
  r.drenar()
  assert ej == []
  assert params.escritos == []


def test_disarm_all_pasa_con_interruptor():
  r, pub, ej = _router(_Params({"OrbitRemoteOff": True}))
  res = r.handle_payload(TOPIC, _sobre("disarm_all"))
  assert res.aceptado
  r.drenar()
  assert ej == ["disarm_all"]
  assert (Phase.APPLIED, "OK") in _terminal(pub, res.cmd_id)


def test_v1_por_submit_local_tambien_remote_off():
  r, pub, ej = _router(_Params({"OrbitRemoteOff": True}))
  res = r.submit_local("lane_change", {"direction": "left"})
  assert res.reason == "REMOTE_OFF"
  assert mando_local.get_mando_local().filas()[0]["o"] == "v1"


def test_ventana_de_activacion_relee_en_ejecutar():
  params = _Params({"OrbitRemoteOff": False})
  r, pub, ej = _router(params)
  res = r.handle_payload(TOPIC, _sobre())
  assert res.aceptado
  params.valores["OrbitRemoteOff"] = True
  r.drenar()
  assert ej == []
  assert _terminal(pub, res.cmd_id) == [(Phase.REJECTED, "REMOTE_OFF")]


def test_interruptor_durante_el_handler_desarma_despues():
  # La pantalla activa el interruptor (y hace su disarm_all) mientras el handler corre:
  # el worker vuelve a desarmar despues, para que lo ultimo escrito sea el neutro.
  params = _Params({"OrbitRemoteOff": False})
  r, pub, ej = _router(params)

  def handler(cmd):
    ej.append(cmd.verb)
    params.valores["OrbitRemoteOff"] = True

  r.register_handler("lane_change", handler)
  r.register_handler("disarm_all", lambda cmd: ej.append("disarm_all"))
  res = r.handle_payload(TOPIC, _sobre())
  assert res.aceptado
  r.drenar()
  assert ej == ["lane_change", "disarm_all"]
  assert r.store.snapshot().get("deadline_mono") == 0.0
  assert _terminal(pub, res.cmd_id) == [(Phase.REJECTED, "REMOTE_OFF")]


def test_sin_params_inyectado_usa_params_real():
  r, _, _ = _router(None)
  assert r._remoto_apagado() is False


# ---------------------------------------------------------------- registro

def test_registro_dedup_y_tope():
  m = MandoLocal()
  for _ in range(10):
    m.anotar("v2", "lane_change", "rejected", "REMOTE_OFF")
  filas = m.filas()
  assert len(filas) == 1 and filas[0]["n"] == 10
  for i in range(60):
    m.anotar("v2", "lane_change" if i % 2 else "disarm_all", "applied", "OK")
  filas = m.filas()
  assert len(filas) == 50
  assert filas[0]["v"] == "lane_change"   # la mas nueva primero (i=59)


def test_registro_sanea_verbo_y_motivo():
  m = MandoLocal()
  m.anotar("v2", "LLAMA AL 600...", "rejected", "TU COCHE ES MIO")
  m.anotar("v2", "lane_change", "rejected", "GATE_ENGAGED")
  m.anotar("v2", "lane_change", "rejected", "GATE_<script>")
  m.anotar("cfg", "cfg", "held", "REMOTE_OFF")
  m.anotar("v2", "lane_change", "fase-rara", "OK")
  filas = m.filas()
  assert [(f["v"], f["r"]) for f in reversed(filas)] == [
    ("desconocido", ""), ("lane_change", "GATE_ENGAGED"), ("lane_change", ""), ("cfg", "REMOTE_OFF")]


def test_volcar_cada_60_s_y_cargar(monkeypatch):
  reloj = [1000.0]
  monkeypatch.setattr(mando_local, "_mono", lambda: reloj[0])
  params = _Params()
  m = MandoLocal()
  m.volcar(params)
  assert params.escritos == []           # sin cambios no escribe
  m.anotar("v2", "lane_change", "applied", "OK")
  m.volcar(params)
  assert params.escritos == ["OrbitRemoteLog"]
  m.anotar("v2", "disarm_all", "applied", "OK")
  reloj[0] += 30
  m.volcar(params)
  assert len(params.escritos) == 1
  reloj[0] += 31
  m.volcar(params)
  assert len(params.escritos) == 2
  datos = json.loads(params.valores["OrbitRemoteLog"])
  assert [d["v"] for d in datos] == ["disarm_all", "lane_change"]

  otro = MandoLocal()
  otro.anotar("v2", "set_mode", "applied", "OK")
  otro.cargar(params)
  assert [f["v"] for f in otro.filas()] == ["set_mode", "disarm_all", "lane_change"]


def test_cargar_ignora_basura():
  m = MandoLocal()
  m.cargar(_Params({"OrbitRemoteLog": "no es json"}))
  m.cargar(_Params({"OrbitRemoteLog": json.dumps([{"o": "v2", "v": "x", "f": "applied", "r": "", "t": 1, "n": 0},
                                                   {"o": "v2", "v": "lane_change", "f": "applied", "r": "", "t": 1,
                                                    "n": 2}, 5])}))
  assert [f["n"] for f in m.filas()] == [2]


# ---------------------------------------------------------------- escritores y sunnylinkd

def test_nadie_en_orbit_escribe_el_interruptor():
  patron = re.compile(r"""put(_bool)?\(\s*["']OrbitRemoteOff["']""")
  culpables = [str(p) for p in (RAIZ / "orbit").rglob("*.py") if "test" not in p.parts
               and patron.search(p.read_text(encoding="utf-8"))]
  assert culpables == []


CLAVES_BLOQUEADAS = {"OrbitRemoteOff", "OrbitRemoteLog", "OrbitPrivacyMute", "OrbitCommandMode", "OrbitBenchArmed",
                     "OrbitBenchExpiry", "OrbitSteerModeLocal", "SteerTorqueMode"}


def test_sunnylinkd_bloquea_las_claves_de_orbit():
  arbol = ast.parse((RAIZ / "sunnypilot/sunnylink/athena/sunnylinkd.py").read_text(encoding="utf-8"))
  bloqueados = None
  for nodo in ast.walk(arbol):
    if isinstance(nodo, ast.Assign) and any(getattr(t, "id", "") == "BLOCKED_PARAMS" for t in nodo.targets):
      bloqueados = ast.literal_eval(nodo.value)
  assert bloqueados is not None and CLAVES_BLOQUEADAS <= bloqueados


def test_sunnylinkd_saveparams_no_toca_el_interruptor(monkeypatch):
  sunnylinkd = pytest.importorskip("openpilot.sunnypilot.sunnylink.athena.sunnylinkd")
  guardados = []
  monkeypatch.setattr(sunnylinkd, "save_param_from_base64_encoded_string",
                      lambda k, v, compression=False: guardados.append(k))
  sunnylinkd.saveParams(dict.fromkeys(CLAVES_BLOQUEADAS, "MA=="))
  assert guardados == []
