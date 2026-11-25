"""Factoria de conexion MQTT (orbit/conexion_mqtt.py): Funnel con credencial o legacy.

Lo que fijan estos tests:

    destino() ............ sin host -> legacy; sin reloj o sin clave -> legacy si lo hay, si no
                           funnel (que fallara); 3 fallos -> legacy 600 s y luego funnel;
                           legacy.activo=false -> nunca legacy; mqtts -> tcp/8443, wss ->
                           websockets/443//mqtt.
    Que es un fallo ...... connect() que lanza, rc != 0 y un error HTTPS de la credencial
                           cuentan (una vez, no dos con el rc 5); on_disconnect no; 429/503 no;
                           key_unknown/key_mismatch -> legacy al momento.
    Sin atascos .......... 180 s en funnel sin un rc 0 -> legacy, cuente o no cada fallo (429 +
                           rc 5, cierres antes del CONNACK). Una peticion de credencial cada
                           60 s como mucho, o lo que diga Retry-After.
    Credencial ........... JWT con claims exactos y 600 s; POST https://h/api/device/mqtt-credential
                           con cabecera JWT y cuerpo exacto; _pre_connect nunca lanza; rc 5 ->
                           el siguiente cuerpo lleva reintento_auth; legacy:false del servidor
                           se persiste en /data.
    client_id ............ nunca el dongle a secas, nunca repetido.
"""
import io
import json
import urllib.error

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from openpilot.orbit import config_broker as cb
from openpilot.orbit import conexion_mqtt as cm

DONGLE = "abc123def4567890"
HOST = "coche.tail0.ts.net"


def _par_ec():
  k = ec.generate_private_key(ec.SECP256R1())
  priv = k.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                         serialization.NoEncryption()).decode()
  pub = k.public_key().public_bytes(serialization.Encoding.PEM,
                                    serialization.PublicFormat.SubjectPublicKeyInfo).decode()
  return priv, pub


PRIV, PUB = _par_ec()


class Reloj:
  def __init__(self):
    self.t = 1000.0

  def __call__(self):
    return self.t


class Resp:
  def __init__(self, data, status=200):
    self.status = status
    self._b = json.dumps(data).encode()

  def read(self):
    return self._b

  def __enter__(self):
    return self

  def __exit__(self, *a):
    return False


class Abrir:
  """Sustituto de urlopen: guarda las peticiones y responde lo que haya en la cola."""
  def __init__(self, *respuestas):
    self.respuestas = list(respuestas)
    self.peticiones = []

  def __call__(self, req, timeout):
    self.peticiones.append(req)
    r = self.respuestas.pop(0) if len(self.respuestas) > 1 else self.respuestas[0]
    if isinstance(r, Exception):
      raise r
    return r


def _http_error(code, reason=None, retry_after=None):
  cuerpo = json.dumps({"error": "x", "reason": reason} if reason else {"error": "x"}).encode()
  cabeceras = {"Retry-After": str(retry_after)} if retry_after is not None else {}
  return urllib.error.HTTPError("https://h", code, "err", cabeceras, io.BytesIO(cuerpo))


def _ok(password="p" * 43, legacy=True):
  return Resp({"username": DONGLE, "password": password, "renovar_en_s": 86400, "legacy": legacy})


class ClienteFalso:
  def __init__(self):
    self.credenciales = []

  def username_pw_set(self, u, p=None):
    self.credenciales.append((u, p))


@pytest.fixture(autouse=True)
def aislar_conexion_mqtt():
  """Anula el aislamiento de orbit/test/conftest.py: este fichero prueba la factoria de verdad."""


@pytest.fixture
def entorno(tmp_path, monkeypatch):
  plantilla = tmp_path / "arbol" / "config_mqtt.json"
  plantilla.parent.mkdir()
  datos = tmp_path / "data"
  datos.mkdir()
  monkeypatch.setattr(cb, "RUTA_PLANTILLA", str(plantilla))
  monkeypatch.setattr(cb, "DIR_PERSISTENTE", str(datos))
  monkeypatch.setattr(cb, "RUTA_PERSISTENTE", str(datos / "orbit_config_mqtt.json"))
  monkeypatch.setattr(cb, "_migracion_hecha", True)
  monkeypatch.setattr(cm, "RUTA_FUNNEL_OK", str(datos / "orbit_funnel_ok"))
  reloj = Reloj()
  monkeypatch.setattr(cm, "_reloj_mono", reloj)
  monkeypatch.setattr(cm, "reloj_valido", lambda: True)
  monkeypatch.setattr(cm, "get_key_pair", lambda: ("ES256", PRIV, PUB))
  cm.reiniciar_estado()

  def config(broker="83.61.25.38", host=HOST, transporte="mqtts", legacy=True, **servidor):
    plantilla.write_text(json.dumps({"broker": broker, "broker_port": 1883, "backend_port": 8010,
                                     "username": "", "password": "",
                                     "servidor": {"host": host, "transporte": transporte, **servidor},
                                     "legacy": {"activo": legacy}}))
    cm.reiniciar_estado()

  config()
  yield config, reloj, datos
  cm.reiniciar_estado()


# --------------------------------------------------------------------------- destino()

def test_sin_host_va_por_legacy(entorno):
  config, _, _ = entorno
  config(host="")
  d = cm.destino()
  assert (d.enlace, d.host, d.puerto, d.transporte, d.tls, d.motivo) == ("legacy", "83.61.25.38", 1883, "tcp", False, "sin_servidor")


def test_sin_host_ni_broker_no_hay_destino(entorno):
  config, _, _ = entorno
  config(host="", broker="")
  assert cm.destino() is None


def test_mqtts_es_tcp_8443(entorno):
  d = cm.destino()
  assert (d.enlace, d.host, d.puerto, d.transporte, d.tls, d.motivo) == ("funnel", HOST, 8443, "tcp", True, "ok")


def test_wss_es_websockets_443_mqtt(entorno):
  config, _, _ = entorno
  config(transporte="wss")
  d = cm.destino()
  assert (d.enlace, d.puerto, d.transporte, d.path) == ("funnel", 443, "websockets", "/mqtt")


@pytest.mark.parametrize("legacy,esperado", [(True, "legacy"), (False, "funnel")])
def test_sin_reloj(entorno, monkeypatch, legacy, esperado):
  config, _, _ = entorno
  config(legacy=legacy)
  monkeypatch.setattr(cm, "reloj_valido", lambda: False)
  d = cm.destino()
  assert (d.enlace, d.motivo) == (esperado, "sin_reloj")


@pytest.mark.parametrize("legacy,esperado", [(True, "legacy"), (False, "funnel")])
def test_sin_clave(entorno, monkeypatch, legacy, esperado):
  config, _, _ = entorno
  config(legacy=legacy)
  monkeypatch.setattr(cm, "get_key_pair", lambda: (None, None, None))
  d = cm.destino()
  assert (d.enlace, d.motivo) == (esperado, "sin_clave")
  # un None no se cachea: cuando aparece la clave, funnel
  monkeypatch.setattr(cm, "get_key_pair", lambda: ("ES256", PRIV, PUB))
  assert cm.destino().enlace == "funnel"


def test_tres_fallos_legacy_y_a_los_601_s_funnel(entorno):
  _, reloj, _ = entorno
  d = cm.destino()
  cm.notificar(d, False)
  cm.notificar(d, False)
  assert cm.destino().enlace == "funnel"
  cm.notificar(d, False)
  l = cm.destino()
  assert (l.enlace, l.motivo) == ("legacy", "fallos")
  reloj.t += 599
  assert cm.destino().enlace == "legacy"
  reloj.t += 2
  assert cm.destino().enlace == "funnel"


def test_legacy_inactivo_nunca_es_legacy(entorno, monkeypatch):
  config, _, _ = entorno
  config(legacy=False)
  d = cm.destino()
  for _ in range(5):
    cm.notificar(d, False)
  assert cm.destino().enlace == "funnel"
  config(legacy=False, host="")
  assert cm.destino() is None


def test_el_motivo_no_entra_en_la_igualdad():
  a = cm.Destino("funnel", "h", 8443, "tcp", True, "", "ok")
  assert a == cm.Destino("funnel", "h", 8443, "tcp", True, "", "sin_reloj")


# -------------------------------------------------------------------- que es un fallo

def test_tres_on_disconnect_siguen_en_funnel(entorno):
  # on_disconnect no llama a notificar; un ok intermedio resetea los fallos
  d = cm.destino()
  cm.notificar(d, False)
  cm.notificar(d, False)
  cm.notificar(d, True, 0)
  cm.notificar(d, False)
  assert cm.destino().enlace == "funnel"
  assert cm.enlace_actual() == "funnel"


def test_ok_por_funnel_marca_funnel_ok(entorno):
  _, _, datos = entorno
  assert not cm.funnel_ok()
  cm.notificar(cm.destino(), True, 0)
  assert cm.funnel_ok() and (datos / "orbit_funnel_ok").exists()


def test_ok_por_legacy_no_marca_funnel_ok(entorno):
  config, _, _ = entorno
  config(host="")
  cm.notificar(cm.destino(), True, 0)
  assert cm.enlace_actual() == "legacy"
  assert not cm.funnel_ok()


@pytest.mark.parametrize("codigo", [429, 503])
def test_credencial_429_o_503_tres_veces_sigue_en_funnel(entorno, monkeypatch, codigo):
  abrir = Abrir(_http_error(codigo))
  monkeypatch.setattr(cm, "_abrir_url", abrir)
  d = cm.destino()
  for _ in range(3):
    cliente = ClienteFalso()
    cm._pre_connect_de(d, DONGLE)(cliente, None)
    assert cliente.credenciales == [(DONGLE, "")]
    cm.notificar(d, False, 5)   # el broker rechaza la contrasena vacia
  assert cm.destino().enlace == "funnel"


@pytest.mark.parametrize("motivo", ["key_unknown", "key_mismatch"])
def test_clave_rechazada_legacy_al_momento(entorno, monkeypatch, motivo):
  monkeypatch.setattr(cm, "_abrir_url", Abrir(_http_error(403, motivo)))
  d = cm.destino()
  cm._pre_connect_de(d, DONGLE)(ClienteFalso(), None)
  l = cm.destino()
  assert (l.enlace, l.motivo) == ("legacy", "clave_rechazada")


@pytest.mark.parametrize("error", [_http_error(404), _http_error(500), urllib.error.URLError(OSError("sin red"))],
                         ids=["404", "500", "red"])
def test_otro_error_de_credencial_cuenta_una_vez(entorno, monkeypatch, error):
  _, reloj, _ = entorno
  abrir = Abrir(error)
  monkeypatch.setattr(cm, "_abrir_url", abrir)
  d = cm.destino()
  for i in range(3):
    assert cm.destino().enlace == "funnel", i
    cm._pre_connect_de(d, DONGLE)(ClienteFalso(), None)
    cm.notificar(d, False, 5)   # el rc 5 de la contrasena vacia no suma otra vez
    reloj.t += cm.ESPERA_CREDENCIAL_S
  assert len(abrir.peticiones) == 3
  assert cm.destino().enlace == "legacy"


def test_429_con_rc5_sin_fin_acaba_en_legacy_y_respeta_retry_after(entorno, monkeypatch):
  # El coche no puede quedarse en funnel sin conexion ni mantener saturado el limitador.
  _, reloj, _ = entorno
  abrir = Abrir(_http_error(429, retry_after=120))
  monkeypatch.setattr(cm, "_abrir_url", abrir)
  d = cm.destino()
  inicio = reloj.t
  while cm.destino().enlace == "funnel":
    assert reloj.t - inicio <= cm.SIN_CONEXION_S, "atascado en funnel"
    cm._pre_connect_de(d, DONGLE)(ClienteFalso(), None)
    cm.notificar(d, False, 5)
    reloj.t += 10
  assert reloj.t - inicio >= cm.SIN_CONEXION_S
  assert len(abrir.peticiones) == 2, "una a los 0 s y otra tras el Retry-After de 120 s"


def test_credencial_como_mucho_una_cada_60_s(entorno, monkeypatch):
  _, reloj, _ = entorno
  abrir = Abrir(_http_error(503))
  monkeypatch.setattr(cm, "_abrir_url", abrir)
  d = cm.destino()
  for _ in range(6):
    cliente = ClienteFalso()
    cm._pre_connect_de(d, DONGLE)(cliente, None)
    assert cliente.credenciales == [(DONGLE, "")]
    reloj.t += 10
  assert len(abrir.peticiones) == 1
  reloj.t += cm.ESPERA_CREDENCIAL_S
  cm._pre_connect_de(d, DONGLE)(ClienteFalso(), None)
  assert len(abrir.peticiones) == 2


def test_cierres_antes_del_connack_acaban_en_legacy(entorno):
  _, reloj, _ = entorno
  d = cm.destino()
  cm.desconectado(d, 0)                  # un disconnect() propio no arranca el reloj
  reloj.t += cm.SIN_CONEXION_S
  cm.desconectado(d, 7)
  reloj.t += cm.SIN_CONEXION_S - 1
  cm.desconectado(d, 7)
  assert cm.destino().enlace == "funnel"
  reloj.t += 1
  cm.desconectado(d, 7)
  l = cm.destino()
  assert (l.enlace, l.motivo) == ("legacy", "fallos")


def test_un_rc0_reinicia_el_reloj_de_sin_conexion(entorno):
  _, reloj, _ = entorno
  d = cm.destino()
  cm.desconectado(d, 7)
  reloj.t += cm.SIN_CONEXION_S - 1
  cm.notificar(d, True, 0)
  reloj.t += 2
  cm.desconectado(d, 7)
  assert cm.destino().enlace == "funnel"


# ------------------------------------------------------------------------- credencial

def test_jwt_claims_exactos_y_verificable():
  tok = cm.jwt_credencial(DONGLE, "ES256", PRIV, 1_700_000_000)
  claims = jwt.decode(tok, PUB, algorithms=["ES256"], options={"verify_exp": False})
  assert claims == {"identity": DONGLE, "orbit": "mqtt", "iat": 1_700_000_000, "exp": 1_700_000_600}


def test_pedir_credencial_url_cabecera_y_cuerpo():
  abrir = Abrir(_ok("secreto"))
  u, p = cm.pedir_credencial("https://h", DONGLE, "ES256", PRIV, PUB, False, abrir=abrir, ahora_s=1_700_000_000)
  assert (u, p) == (DONGLE, "secreto")
  req = abrir.peticiones[0]
  assert req.full_url == "https://h/api/device/mqtt-credential"
  assert req.get_method() == "POST"
  auth = req.get_header("Authorization")
  assert auth.startswith("JWT ")
  assert jwt.decode(auth[4:], PUB, algorithms=["ES256"], options={"verify_exp": False})["identity"] == DONGLE
  assert json.loads(req.data) == {"dongle_id": DONGLE, "pubkey": PUB, "key_alg": "ES256", "reintento_auth": False}


@pytest.mark.parametrize("error,motivo", [
  (_http_error(401, "clock"), "clock"),
  (_http_error(401, "signature"), "signature"),
  (_http_error(403, "key_unknown"), "key_unknown"),
  (_http_error(500), "http_500"),
  (urllib.error.URLError(OSError("sin red")), "red"),
  (TimeoutError(), "red"),
])
def test_pedir_credencial_errores(error, motivo):
  with pytest.raises(cm.ErrorCredencial) as e:
    cm.pedir_credencial("https://h", DONGLE, "ES256", PRIV, PUB, False, abrir=Abrir(error))
  assert e.value.motivo == motivo


def test_pre_connect_nunca_lanza(entorno, monkeypatch):
  def revienta(req, timeout):
    raise RuntimeError("lo que sea")
  monkeypatch.setattr(cm, "_abrir_url", revienta)
  d = cm.destino()
  cliente = ClienteFalso()
  cm._pre_connect_de(d, DONGLE)(cliente, None)
  assert cliente.credenciales == [(DONGLE, "")]
  monkeypatch.setattr(cm, "get_key_pair", lambda: (None, None, None))
  cm.reiniciar_estado()
  cm._pre_connect_de(d, DONGLE)(cliente, None)
  assert cliente.credenciales[-1] == (DONGLE, "")


def test_pre_connect_usa_la_cache_y_rc5_pide_con_reintento_auth(entorno, monkeypatch):
  _, reloj, _ = entorno
  abrir = Abrir(_ok("uno"))
  monkeypatch.setattr(cm, "_abrir_url", abrir)
  d = cm.destino()
  cliente = ClienteFalso()
  pre = cm._pre_connect_de(d, DONGLE)
  pre(cliente, None)
  pre(cliente, None)
  assert cliente.credenciales == [(DONGLE, "uno"), (DONGLE, "uno")]
  assert len(abrir.peticiones) == 1
  assert abrir.peticiones[0].full_url == f"https://{HOST}/api/device/mqtt-credential"
  cm.notificar(d, False, 5)
  reloj.t += cm.ESPERA_CREDENCIAL_S   # como mucho una peticion por minuto
  pre(cliente, None)
  assert len(abrir.peticiones) == 2
  assert json.loads(abrir.peticiones[1].data)["reintento_auth"] is True
  pre(cliente, None)  # tras un 200 vuelve a False (y a la cache)
  assert len(abrir.peticiones) == 2


def test_legacy_false_del_servidor_se_persiste_y_nunca_mas_legacy(entorno, monkeypatch):
  _, _, datos = entorno
  monkeypatch.setattr(cm, "_abrir_url", Abrir(_ok(legacy=False)))
  d = cm.destino()
  cm._pre_connect_de(d, DONGLE)(ClienteFalso(), None)
  assert json.loads((datos / "orbit_config_mqtt.json").read_text())["legacy"] == {"activo": False}
  for _ in range(5):
    cm.notificar(d, False)
  assert cm.destino().enlace == "funnel"


def test_contexto_tls_carga_certifi():
  import certifi
  ctx = cm.contexto_tls()
  assert ctx.verify_mode.name == "CERT_REQUIRED"
  assert ctx.cert_store_stats()["x509_ca"] > 0
  assert certifi.where()


def test_huella_local():
  import hashlib
  cm.reiniciar_estado()
  orig = cm.get_key_pair
  try:
    cm.get_key_pair = lambda: ("ES256", PRIV, PUB)
    assert cm.huella_local() == hashlib.sha256(PUB.encode()).hexdigest()[:16]
  finally:
    cm.get_key_pair = orig
    cm.reiniciar_estado()


# --------------------------------------------------------------------------- clientes
# paho avisa de la API de callbacks v1, la que usan los tres clientes del firmware.

@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_client_id_funnel_nunca_el_dongle_ni_repetido(entorno):
  d = cm.destino()
  a = cm.crear_cliente(d, DONGLE)
  b = cm.crear_cliente(d, DONGLE)
  ida, idb = a._client_id.decode(), b._client_id.decode()
  assert ida != DONGLE and idb != DONGLE and ida != idb
  assert ida.startswith(DONGLE + "-")
  assert a.on_pre_connect is not None
  assert a._transport == "tcp" and a._ssl


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_cliente_wss_lleva_path(entorno):
  config, _, _ = entorno
  config(transporte="wss")
  c = cm.crear_cliente(cm.destino(), DONGLE)
  assert c._transport == "websockets" and c._websocket_path == "/mqtt"


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_cliente_legacy_es_el_de_siempre(entorno):
  config, _, _ = entorno
  config(host="")
  c = cm.crear_cliente(cm.destino(), DONGLE)
  assert c._transport == "tcp" and not c._ssl and c.on_pre_connect is None
  assert c._username is None
