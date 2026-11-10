"""Desvinculo desde el propio comma, lado dispositivo (contrato C1, C2, C3, C5).

El broker es abierto: la unica prueba de que la peticion viene del comma es la firma con
su clave privada. Aqui se fija lo que el firmware publica (caps con la publica, JWT con
EXACTAMENTE los claims del contrato), como guarda el nonce, y que hace con cada respuesta.
"""
import json

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa

from openpilot.orbit import mqtt_comandos
from openpilot.orbit import mqtt_envio_general as envio_mod
from openpilot.orbit.command_spec import TOPIC_CAPS
from openpilot.orbit.mqtt_envio_general import MQTTEnvioGeneral
from openpilot.orbit.test.test_mando_v1_por_router import (DONGLE, V1, _ClienteFalso, _comandos, _entregar, _ParamsFalsos)

NONCE = "nonce-de-prueba-123"


def _par(alg):
  clave = rsa.generate_private_key(65537, 2048) if alg == "RS256" else ec.generate_private_key(ec.SECP256R1())
  privada = clave.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                serialization.NoEncryption()).decode()
  publica = clave.public_key().public_bytes(serialization.Encoding.PEM,
                                            serialization.PublicFormat.SubjectPublicKeyInfo).decode()
  return alg, privada, publica


@pytest.fixture(scope="module")
def pares():
  return {a: _par(a) for a in ("RS256", "ES256")}


@pytest.fixture
def con_clave(monkeypatch, pares):
  par = pares["ES256"]
  monkeypatch.setattr(mqtt_comandos, "get_key_pair", lambda: par)
  monkeypatch.setattr(envio_mod, "get_key_pair", lambda: par)
  return par


@pytest.fixture
def sin_clave(monkeypatch):
  monkeypatch.setattr(mqtt_comandos, "get_key_pair", lambda: (None, None, None))
  monkeypatch.setattr(envio_mod, "get_key_pair", lambda: (None, None, None))


def _caps(c):
  assert c.maybe_publish_caps(forzar=True)
  return json.loads(next(p for t, p, *_ in c.mqttc.publicados if t == TOPIC_CAPS.format(DONGLE)))


def _envio(params, conectado=True, dongle_valido=True):
  e = object.__new__(MQTTEnvioGeneral)
  e.params = params
  e.conectado = conectado
  e.dongle_valido = dongle_valido
  e.DongleID = DONGLE
  e.mqttc = _ClienteFalso()
  e._last_unlink = float("-inf")
  e.UNLINK_RETRY_SECS = 10.0
  return e


def _resultado(params):
  return json.loads(params.valores["OrbitUnlinkResult"])


# --------------------------------------------------------------------------- C1: caps

@pytest.mark.parametrize("alg", ["RS256", "ES256"])
def test_caps_lleva_la_clave_publica_y_el_algoritmo(monkeypatch, pares, alg):
  monkeypatch.setattr(mqtt_comandos, "get_key_pair", lambda: pares[alg])
  d = _caps(_comandos(verde=True))
  assert d["pubkey"] == pares[alg][2] and d["key_alg"] == alg


def test_caps_sin_clave_no_lleva_pubkey_ni_alg(sin_clave):
  d = _caps(_comandos(verde=True))
  assert "pubkey" not in d and "key_alg" not in d and d["v"] == 2


def test_la_clave_se_lee_una_vez_y_la_ausencia_se_reintenta_con_pausa(monkeypatch, pares):
  llamadas = []
  respuestas = [(None, None, None), pares["ES256"]]

  def _lee():
    llamadas.append(1)
    return respuestas[min(len(llamadas) - 1, 1)]
  monkeypatch.setattr(mqtt_comandos, "get_key_pair", _lee)
  ahora = [1000.0]
  monkeypatch.setattr(mqtt_comandos.time, "monotonic", lambda: ahora[0])
  c = _comandos(verde=True)
  assert c._clave_publica() == (None, None) and c._clave_publica() == (None, None)
  assert len(llamadas) == 1                      # sin clave: no se relee en cada tick
  ahora[0] += c.CLAVE_REINTENTO_S + 1
  assert c._clave_publica()[0] == "ES256" and len(llamadas) == 2
  assert c._clave_publica()[0] == "ES256" and len(llamadas) == 2   # con clave: cacheada


# --------------------------------------------------------------------------- C2: nonce

def _ack(c, **campos):
  _entregar(c, f"{V1}/enroll_ack", json.dumps(campos), retain=True)


def test_claimed_true_con_nonce_lo_guarda():
  c = _comandos(params=_ParamsFalsos())
  _ack(c, claimed=True, user_id=7, user_name="Ana", unlink_nonce=NONCE)
  assert c.params.valores["OrbitUnlinkNonce"] == NONCE and c.params.valores["OrbitClaimed"] is True


@pytest.mark.parametrize("nonce", [None, "", 5, "x" * 200])
def test_claimed_true_con_nonce_ausente_o_malo_no_toca_el_guardado(nonce):
  c = _comandos(params=_ParamsFalsos({"OrbitUnlinkNonce": "viejo"}))
  _ack(c, claimed=True, user_id=7, user_name="Ana", unlink_nonce=nonce)
  assert c.params.valores["OrbitUnlinkNonce"] == "viejo"


def test_claimed_false_borra_nonce_y_peticion_y_escribe_ok():
  c = _comandos(params=_ParamsFalsos({"OrbitClaimed": True, "OrbitUnlinkNonce": NONCE, "OrbitUnlinkRequest": True}))
  _ack(c, claimed=False)
  v = c.params.valores
  assert "OrbitUnlinkNonce" not in v and "OrbitUnlinkRequest" not in v
  assert v["OrbitClaimed"] is False and v["OrbitEnrollRegen"] is True
  assert _resultado(c.params)["ok"] is True


# --------------------------------------------------------------------------- C3: peticion

@pytest.mark.parametrize("alg", ["RS256", "ES256"])
def test_con_peticion_nonce_clave_y_conexion_publica_el_jwt_del_contrato(monkeypatch, pares, alg):
  monkeypatch.setattr(envio_mod, "get_key_pair", lambda: pares[alg])
  e = _envio(_ParamsFalsos({"OrbitUnlinkRequest": True, "OrbitUnlinkNonce": NONCE}))
  e._maybe_send_unlink()
  (topic, payload, qos, retain), = e.mqttc.publicados
  assert topic == f"telemetry_mqtt/{DONGLE}/unlink" and qos == 1 and retain is False
  d = json.loads(payload)
  assert set(d) == {"v", "token"} and d["v"] == 1
  claims = jwt.decode(d["token"], pares[alg][2], algorithms=[alg], options={"verify_exp": False})
  assert claims == {"identity": DONGLE, "orbit": "unlink", "nonce": NONCE}   # exactos, sin exp
  assert jwt.get_unverified_header(d["token"])["alg"] == alg


def test_sin_peticion_no_publica_nada(con_clave):
  e = _envio(_ParamsFalsos({"OrbitUnlinkNonce": NONCE}))
  e._maybe_send_unlink()
  assert e.mqttc.publicados == []


def test_sin_clave_no_publica_y_escribe_el_resultado(sin_clave):
  e = _envio(_ParamsFalsos({"OrbitUnlinkRequest": True, "OrbitUnlinkNonce": NONCE}))
  e._maybe_send_unlink()
  assert e.mqttc.publicados == [] and "OrbitUnlinkRequest" not in e.params.valores
  assert _resultado(e.params)["ok"] is False and _resultado(e.params)["reason"] == "no_key"


def test_sin_nonce_no_publica_y_escribe_el_resultado(con_clave):
  e = _envio(_ParamsFalsos({"OrbitUnlinkRequest": True}))
  e._maybe_send_unlink()
  assert e.mqttc.publicados == [] and "OrbitUnlinkRequest" not in e.params.valores
  assert _resultado(e.params)["reason"] == "no_nonce"


def test_sin_conexion_espera_y_conserva_la_peticion(con_clave):
  e = _envio(_ParamsFalsos({"OrbitUnlinkRequest": True, "OrbitUnlinkNonce": NONCE}), conectado=False)
  e._maybe_send_unlink()
  assert e.mqttc.publicados == [] and e.params.valores["OrbitUnlinkRequest"] is True
  assert "OrbitUnlinkResult" not in e.params.valores


def test_reintenta_cada_10_s_y_no_antes(con_clave, monkeypatch):
  ahora = [500.0]
  monkeypatch.setattr(envio_mod.time, "monotonic", lambda: ahora[0])
  e = _envio(_ParamsFalsos({"OrbitUnlinkRequest": True, "OrbitUnlinkNonce": NONCE}))
  e._maybe_send_unlink()
  assert len(e.mqttc.publicados) == 1
  ahora[0] += 9.9
  e._maybe_send_unlink()
  assert len(e.mqttc.publicados) == 1
  ahora[0] += 0.2
  e._maybe_send_unlink()
  assert len(e.mqttc.publicados) == 2


def test_un_fallo_al_publicar_no_rompe_el_bucle(con_clave):
  e = _envio(_ParamsFalsos({"OrbitUnlinkRequest": True, "OrbitUnlinkNonce": NONCE}))

  def _roto(*a, **k):
    raise OSError("socket")
  e.mqttc.publish = _roto
  e._maybe_send_unlink()    # no lanza


# --------------------------------------------------------------------------- C4/C5: unlink_ack

def _unlink_ack(c, **campos):
  _entregar(c, f"{V1}/unlink_ack", json.dumps(campos))


def _con_peticion():
  return _comandos(params=_ParamsFalsos({"OrbitClaimed": True, "OrbitUnlinkRequest": True, "OrbitUnlinkNonce": NONCE}))


@pytest.mark.parametrize("motivo", ["no_key", "bad_signature", "bad_nonce", "bad_request"])
def test_unlink_ack_rechazado_escribe_el_resultado_y_borra_la_peticion(motivo):
  c = _con_peticion()
  _unlink_ack(c, ok=False, reason=motivo, ts=1)
  assert "OrbitUnlinkRequest" not in c.params.valores
  assert _resultado(c.params)["ok"] is False and _resultado(c.params)["reason"] == motivo
  assert c.params.valores["OrbitClaimed"] is True and c.params.valores["OrbitUnlinkNonce"] == NONCE


def test_unlink_ack_ok_limpia_peticion_y_nonce():
  c = _con_peticion()
  _unlink_ack(c, ok=True, ts=1)
  v = c.params.valores
  assert "OrbitUnlinkRequest" not in v and "OrbitUnlinkNonce" not in v and _resultado(c.params)["ok"] is True


def test_unlink_ack_sin_peticion_en_curso_se_ignora():
  c = _comandos(params=_ParamsFalsos({"OrbitUnlinkNonce": NONCE}))
  _unlink_ack(c, ok=False, reason="bad_signature", ts=1)
  _unlink_ack(c, ok=True, ts=1)
  assert "OrbitUnlinkResult" not in c.params.valores and c.params.valores["OrbitUnlinkNonce"] == NONCE


@pytest.mark.parametrize("basura", ['no es json', '[]', '{"ok": "si"}', '{}'])
def test_unlink_ack_mal_formado_no_toca_nada(basura):
  c = _con_peticion()
  _entregar(c, f"{V1}/unlink_ack", basura)
  assert c.params.valores["OrbitUnlinkRequest"] is True and "OrbitUnlinkResult" not in c.params.valores


def test_unlink_ack_retenido_se_descarta():
  c = _con_peticion()
  _entregar(c, f"{V1}/unlink_ack", json.dumps({"ok": True}), retain=True)
  assert c.params.valores["OrbitUnlinkRequest"] is True


def test_la_suscripcion_cubre_unlink_ack():
  c = _comandos()
  c._refrescar_dongle = lambda: None
  suscritos = []

  class _Cliente:
    def subscribe(self, topic, qos=0):
      suscritos.append(topic)
  c._on_connect(_Cliente(), None, None, 0)
  assert f"telemetry_config/{DONGLE}/unlink_ack" in suscritos
