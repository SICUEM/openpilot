import json

import jwt
import pytest

from openpilot.orbit import enroll_v2 as e
from openpilot.orbit import mqtt_envio_general as envio_mod
from openpilot.orbit.command_spec import ArgSpec, CommandSpec, Mode, _args, spec_table_dict, validar_args
from openpilot.orbit.test.test_desvinculo import _envio, _par
from openpilot.orbit.test.test_mando_v1_por_router import DONGLE, _ParamsFalsos

PEM = "-----BEGIN PUBLIC KEY-----\nTEST\n-----END PUBLIC KEY-----\n"


def test_vector_fijo():
  h = e.hash_enrolamiento("0123456789abcdef", "ABCDEFGHJKLMNPQRSTUVWXYZ23", PEM)
  assert h == "7eb5b69fa84c384c37cab4d2151d32033b6983d550c12b345c1e5cbd3dcaf75a"


def test_token_y_alfabeto():
  assert len(e.ALFABETO) == 32 and len(set(e.ALFABETO)) == 32
  t = e.nuevo_token()
  assert len(t) == e.LONGITUD and set(t) <= set(e.ALFABETO)
  assert e.nuevo_token() != t


def test_normalizar():
  assert e.normalizar_codigo(" abcd-efgh\tjk lm ") == "ABCDEFGHJKLM"


def test_url_y_legible():
  t = "ABCDEFGHJKLMNPQRSTUVWXYZ23"
  assert e.url_enrolamiento("d1", t) == f"orbit://enroll?d=d1&c={t}&v=2"
  assert e.url_enrolamiento("d1", "ABCD2345") == "orbit://enroll?d=d1&c=ABCD2345"
  assert e.codigo_legible(t) == "ABCD EFGH JKLM NPQR STUV WXYZ 23"


def test_bookmark_en_spec():
  assert spec_table_dict()["bookmark"]["args"] == {}


def test_str_maximo_compara_longitud():
  spec = CommandSpec(verb="x", mode_min=Mode.OBSERVER, args_schema=_args(n=ArgSpec(tipo=str, maximo=3)))
  assert validar_args(spec, {"n": "abc"})[0] is None
  assert validar_args(spec, {"n": "abcd"})[0] == "RANGE"


# --------------------------------------------------------------- anuncio (C-28.2)

@pytest.fixture(scope="module")
def par_ec():
  return _par("ES256")


def _anunciador(monkeypatch, hw, clave, reloj=True):
  monkeypatch.setattr(envio_mod, "tipo_dispositivo", lambda: hw)
  monkeypatch.setattr(envio_mod, "get_key_pair", lambda: clave[0])
  monkeypatch.setattr(envio_mod.MQTTEnvioGeneral, "_reloj_valido", staticmethod(lambda: reloj))
  env = _envio(_ParamsFalsos())
  env._last_enroll = 0.0
  env._enroll_issued_at = 0.0
  env._pairing_code = None
  env.ENROLL_ANNOUNCE_SECS = 30.0
  env.ENROLL_TTL_S = 600
  return env


def _enrolls(env):
  return [json.loads(p) for t, p, *_ in env.mqttc.publicados if t == f"telemetry_mqtt/{DONGLE}/enroll"]


def test_payload_v2_firmado(monkeypatch, par_ec):
  alg, _, publica = par_ec
  env = _anunciador(monkeypatch, "tizi", [par_ec])
  env._maybe_announce_enroll()
  (p,) = _enrolls(env)
  token = env.params.valores["OrbitPairingCode"]
  assert len(token) == e.LONGITUD and "pairing_code" not in p
  assert p["v"] == 2 and p["pubkey"] == publica and p["key_alg"] == alg and p["hw"] == "tizi"
  assert p["h"] == e.hash_enrolamiento(DONGLE, token, publica)
  claims = jwt.decode(p["sig"], publica, algorithms=[alg])
  assert claims == {"identity": DONGLE, "orbit": "enroll", "h": p["h"], "iat": p["issued_at"] // 1000}
  assert token not in json.dumps(p)


def test_sin_reloj_no_genera_ni_anuncia(monkeypatch, par_ec):
  env = _anunciador(monkeypatch, "mici", [par_ec], reloj=False)
  env._maybe_announce_enroll()
  assert _enrolls(env) == [] and "OrbitPairingCode" not in env.params.valores


def test_pc_sin_clave_es_legacy(monkeypatch):
  env = _anunciador(monkeypatch, "pc", [(None, None, None)], reloj=False)
  env._maybe_announce_enroll()
  (p,) = _enrolls(env)
  assert len(p["pairing_code"]) == 8 and "v" not in p and "sig" not in p
  assert env.params.valores["OrbitPairingCode"] == p["pairing_code"]


def test_mici_sin_clave_no_anuncia_y_reintenta(monkeypatch, par_ec):
  clave = [(None, None, None)]
  env = _anunciador(monkeypatch, "mici", clave)
  env._maybe_announce_enroll()
  assert _enrolls(env) == [] and "OrbitPairingCode" not in env.params.valores
  clave[0] = par_ec                       # el None no se cacheo: ya hay clave
  env._maybe_announce_enroll()
  (p,) = _enrolls(env)
  assert p["v"] == 2 and "pairing_code" not in p
