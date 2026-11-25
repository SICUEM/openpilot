"""Verbo `bookmark` en el router (C-10.6, parte del router). El handler real es de
mqtt_comandos; aqui se usa uno que no hace nada, que es lo que el contrato le pide."""
import json

import pytest

from openpilot.orbit import command_router as router_mod
from openpilot.orbit.command_router import CommandRouter
from openpilot.orbit.command_spec import Phase, ahora_epoch_ms

DONGLE = "0123456789abcdef"
TOPIC = f"orbit/v2/cmd/{DONGLE}"


class _Params:
  def __init__(self):
    self.escritos = []

  def get_bool(self, key, *a, **k):
    return False

  def get(self, key, *a, **k):
    return None

  def put(self, key, *a, **k):
    self.escritos.append(key)

  put_bool = put


class _Gates:
  clock_synced = True
  brand = "ford"
  stale = False

  def __init__(self, onroad=True):
    self.onroad = onroad

  def note_link(self, cuando_mono=None):
    pass

  def evaluate(self, spec, args=None):
    return True, []


@pytest.fixture
def reloj(monkeypatch):
  t = [5000.0]
  monkeypatch.setattr(router_mod, "ahora_mono", lambda: t[0])
  return t


def _router(gates):
  params = _Params()
  pub = []
  r = CommandRouter(DONGLE, gates=gates, params=params, publish=lambda t, p, q, ret: pub.append(json.loads(p)))
  r.register_handler("bookmark", lambda cmd: None)
  return r, pub, params


_N = [0]


def _sobre(args=None):
  _N[0] += 1
  return json.dumps({"v": 2, "id": f"bm-{_N[0]}", "seq": _N[0], "verb": "bookmark", "args": args or {},
                     "ts_ms": ahora_epoch_ms(), "ttl_ms": 10000, "mode": "observador", "actor": {}})


def _final(pub, cmd_id):
  return [p["phase"] for p in pub if p["id"] == cmd_id][-1]


def test_offroad_rechaza_offroad():
  r, _, _ = _router(_Gates(onroad=False))
  res = r.handle_payload(TOPIC, _sobre())
  assert (res.aceptado, res.reason) == (False, "OFFROAD")


def test_sin_gatemonitor_internal_sin_excepcion():
  r, _, _ = _router(None)
  res = r.handle_payload(TOPIC, _sobre())
  assert (res.aceptado, res.reason) == (False, "INTERNAL")


def test_onroad_applied_sin_params(reloj):
  r, pub, params = _router(_Gates())
  res = r.handle_payload(TOPIC, _sobre())
  assert res.aceptado
  r.drenar()
  assert _final(pub, res.cmd_id) == Phase.APPLIED
  assert params.escritos == []


def test_intervalo_minimo_5_s(reloj):
  r, pub, _ = _router(_Gates())
  assert r.handle_payload(TOPIC, _sobre()).aceptado
  reloj[0] += 2.0
  res = r.handle_payload(TOPIC, _sobre())
  assert (res.reason, res.detail) == ("RANGE", "un bookmark cada 5 s")
  reloj[0] += 3.1                     # 5,1 s desde el ultimo ACEPTADO
  assert r.handle_payload(TOPIC, _sobre()).aceptado


def test_rechazo_no_consume_el_intervalo(reloj):
  gates = _Gates(onroad=False)
  r, _, _ = _router(gates)
  assert r.handle_payload(TOPIC, _sobre()).reason == "OFFROAD"
  gates.onroad = True
  assert r.handle_payload(TOPIC, _sobre()).aceptado


def test_args_no_vacios_type():
  r, _, _ = _router(_Gates())
  assert r.handle_payload(TOPIC, _sobre({"note": "hola"})).reason == "TYPE"


def test_diez_bookmarks_solo_applied(reloj):
  r, pub, params = _router(_Gates())
  for _ in range(10):
    assert r.handle_payload(TOPIC, _sobre()).aceptado
    r.drenar()
    reloj[0] += 5.1
  finales = [p["phase"] for p in pub if p["phase"] in (Phase.APPLIED, Phase.REJECTED, Phase.FAILED)]
  assert finales == [Phase.APPLIED] * 10
  assert params.escritos == []


def test_bookmark_no_pisa_el_plano_de_un_lane_change_pendiente(reloj):
  # lane_change (conserva_plano) mantiene activeVerb/cmdId hasta su veredicto; un bookmark
  # aceptado no puede borrarlos ni sustituirlos.
  from openpilot.orbit.command_state import CommandStateStore
  store = CommandStateStore()
  store.begin_command("lane_change", "lc-1", 7, 9999.0)
  r, pub, _ = _router(_Gates())
  r.store = store
  res = r.handle_payload(TOPIC, _sobre())
  assert res.aceptado
  r.drenar()
  assert _final(pub, res.cmd_id) == Phase.APPLIED
  assert (store.active_verb, store.cmd_id, store.deadline_mono) == ("lane_change", "lc-1", 9999.0)
