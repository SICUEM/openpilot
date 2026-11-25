#!/usr/bin/env python3
"""Factoria de la conexion MQTT del firmware ORBIT: Funnel (TLS + credencial) o legacy.

QUE DECIDE

`destino()` elige a donde conectar los clientes paho de ESTE proceso:

    funnel ... servidor.host de la config (mqtts:8443 o wss:443/mqtt), TLS, usuario =
               dongle_id y contrasena que da el backend en POST /api/device/mqtt-credential
               a cambio de un JWT firmado con la clave del dispositivo (la de device_keys).
    legacy ... el broker de siempre (broker/broker_port, anonimo o con username/password),
               solo si legacy.activo y hay broker.

Se cae a legacy sin servidor, sin reloj valido (sin reloj no hay JWT ni TLS), sin clave del
dispositivo, con FALLOS_PARA_LEGACY fallos seguidos de funnel (durante LEGACY_DURANTE_S) y
al momento si el backend dice key_unknown/key_mismatch. Tambien tras SIN_CONEXION_S en funnel
sin ningun on_connect rc 0, cuente o no cada fallo (429/503 de la credencial, cierres antes
del CONNACK que paho solo da por on_disconnect): ningun atasco deja al coche sin enlace. Con
legacy.activo = false nunca.

La credencial se pide como mucho una vez cada ESPERA_CREDENCIAL_S por proceso (o lo que diga
Retry-After, si es mas): los clientes reconectan cada <= 30 s y sin esto el propio coche
mantenia saturado el limitador del backend.

El estado es POR PROCESO (en orbit/manager lo comparten telemetria y mando; en selfdrived,
events_mqtt). Importable sin openpilot: los imports de openpilot.* y de paho van dentro de
las funciones, asi el backend carga este fichero por ruta en su test cruzado.
"""
import hashlib
import json
import os
import secrets
import ssl
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime

try:
  from openpilot.common.swaglog import cloudlog
except ImportError:  # backend o PC sin el entorno completo
  import logging
  cloudlog = logging.getLogger("orbit.conexion_mqtt")

ENLACE_FUNNEL = "funnel"
ENLACE_LEGACY = "legacy"
FALLOS_PARA_LEGACY = 3          # fallos seguidos de funnel antes de caer a legacy
LEGACY_DURANTE_S = 600          # tiempo en legacy antes de reintentar funnel
TTL_JWT_S = 600
TIMEOUT_HTTPS_S = 10
SIN_CONEXION_S = 180            # en funnel sin ningun rc 0 durante esto -> legacy
ESPERA_CREDENCIAL_S = 60        # minimo entre dos peticiones de credencial
RETRY_AFTER_MAX_S = 3600        # tope a lo que pida el backend con Retry-After
RUTA_CREDENCIAL = "/api/device/mqtt-credential"
CONFIG_TTL_S = 5.0
RENOVAR_POR_DEFECTO_S = 86400
# Marca persistente: este coche ya conecto alguna vez por Funnel (mqtt_comandos deja de
# aceptar ordenes por legacy a partir de entonces).
RUTA_FUNNEL_OK = "/data/orbit_funnel_ok"
# Errores de la credencial que no cuentan como fallo de Funnel: nadie debe poder forzar la
# caida a legacy agotando el cupo del dongle.
_NO_CUENTAN = ("http_429", "http_503")
_CLAVE_RECHAZADA = ("key_unknown", "key_mismatch")


@dataclass(frozen=True)
class Destino:
  enlace: str        # "funnel" | "legacy"
  host: str
  puerto: int
  transporte: str    # "tcp" | "websockets" (paho)
  tls: bool
  path: str          # "/mqtt" (solo websockets)
  # "ok" | "sin_servidor" | "sin_reloj" | "sin_clave" | "fallos" | "clave_rechazada".
  # Solo diagnostico: fuera de __eq__ para que un cambio de motivo no reinicie clientes.
  motivo: str = field(default="ok", compare=False)


class ErrorCredencial(Exception):
  """motivo: "red" | "tls" | "clock" | "signature" | "key_mismatch" | "key_unknown" | "http_<n>"
  | "espera" (no se pide: aun no toca). retry_after: segundos que pide el backend, o 0."""

  def __init__(self, motivo: str, retry_after: int = 0):
    super().__init__(motivo)
    self.motivo = motivo
    self.retry_after = retry_after


# ---------------------------------------------------------------- estado del proceso

_lock = threading.RLock()
_reloj_mono = time.monotonic
_cfg: dict | None = None
_cfg_t = float("-inf")
_clave: tuple[str, str, str] | None = None
_fallos = 0
_legacy_hasta = float("-inf")
_motivo_legacy = "fallos"
_enlace = ""
_credenciales: dict[tuple[str, str], tuple[str, float]] = {}
_reintento_auth = False
_ignorar_rc_auth = False
_funnel_desde: float | None = None   # primer fallo de funnel sin un rc 0 despues
_credencial_no_antes = float("-inf")


def reiniciar_estado() -> None:
  """Para tests: olvida config, clave, fallos, credenciales y enlace."""
  global _cfg, _cfg_t, _clave, _fallos, _legacy_hasta, _motivo_legacy, _enlace, _reintento_auth, _ignorar_rc_auth
  global _funnel_desde, _credencial_no_antes
  with _lock:
    _cfg, _cfg_t, _clave = None, float("-inf"), None
    _fallos, _legacy_hasta, _motivo_legacy, _enlace = 0, float("-inf"), "fallos", ""
    _credenciales.clear()
    _reintento_auth = _ignorar_rc_auth = False
    _funnel_desde, _credencial_no_antes = None, float("-inf")


# ------------------------------------------------- dependencias de openpilot (parcheables)

def get_key_pair():
  from openpilot.common.api import get_key_pair as _gkp
  return _gkp()


def reloj_valido() -> bool:
  from openpilot.common.time_helpers import system_time_valid
  return system_time_valid()


def _leer_config() -> dict:
  from openpilot.orbit import config_broker
  return config_broker.leer_config()


def _escribir_config(cambios: dict) -> bool:
  from openpilot.orbit import config_broker
  return config_broker.escribir_config(cambios)


def _config(ahora: float) -> dict:
  global _cfg, _cfg_t
  with _lock:
    if _cfg is None or ahora - _cfg_t >= CONFIG_TTL_S:
      try:
        _cfg = _leer_config()
      except Exception:
        cloudlog.exception("[ORBIT] no se pudo leer la config MQTT")
        _cfg = _cfg or {}
      _cfg_t = ahora
    return _cfg


def _clave_dispositivo() -> tuple[str, str, str] | None:
  """(alg, privada, publica) o None. Una lectura con clave se guarda; un None no (la clave
  aparece tras el registro del comma)."""
  global _clave
  if _clave is None:
    try:
      alg, privada, publica = get_key_pair()
    except Exception:
      cloudlog.exception("[ORBIT] no se pudo leer la clave del dispositivo")
      return None
    if alg and privada and publica:
      _clave = (alg, privada, publica)
  return _clave


def _legacy(cfg: dict, motivo: str) -> Destino | None:
  broker = str(cfg.get("broker") or "").strip()
  legacy = cfg.get("legacy")
  activo = legacy.get("activo", True) if isinstance(legacy, dict) else True
  if not activo or not broker:
    return None
  try:
    puerto = int(cfg.get("broker_port", 1883))
  except (TypeError, ValueError):
    puerto = 1883
  return Destino(ENLACE_LEGACY, broker, puerto, "tcp", False, "", motivo)


def _funnel(servidor: dict, host: str) -> Destino:
  wss = servidor.get("transporte") == "wss"
  try:
    puerto = int(servidor.get("puerto") or (443 if wss else 8443))
  except (TypeError, ValueError):
    puerto = 443 if wss else 8443
  return Destino(ENLACE_FUNNEL, host, puerto, "websockets" if wss else "tcp",
                 bool(servidor.get("tls", True)), str(servidor.get("path") or "/mqtt") if wss else "")


# ------------------------------------------------------------------------- API publica

def destino(ahora_mono: float | None = None) -> Destino | None:
  ahora = _reloj_mono() if ahora_mono is None else ahora_mono
  with _lock:
    cfg = _config(ahora)
    servidor = cfg.get("servidor") if isinstance(cfg.get("servidor"), dict) else {}
    host = str(servidor.get("host") or "").strip()
    if not host:
      return _legacy(cfg, "sin_servidor")
    if ahora < _legacy_hasta:
      d = _legacy(cfg, _motivo_legacy)
      if d is not None:
        return d
    funnel = _funnel(servidor, host)
  # Fuera del lock: reloj y clave tocan disco.
  if not reloj_valido():
    return _legacy(cfg, "sin_reloj") or replace(funnel, motivo="sin_reloj")
  if _clave_dispositivo() is None:
    return _legacy(cfg, "sin_clave") or replace(funnel, motivo="sin_clave")
  return funnel


def enlace_actual() -> str:
  """Ultimo enlace con on_connect rc == 0 en ESTE proceso; "" si ninguno."""
  return _enlace


def funnel_ok() -> bool:
  return os.path.exists(RUTA_FUNNEL_OK)


def huella_local() -> str | None:
  """Huella de la clave publica local; la compara el dueno con /api/admin/enlaces."""
  clave = _clave_dispositivo()
  return hashlib.sha256(clave[2].encode()).hexdigest()[:16] if clave else None


def contexto_tls() -> ssl.SSLContext:
  try:
    import certifi
    return ssl.create_default_context(cafile=certifi.where())
  except ImportError:
    return ssl.create_default_context()


def jwt_credencial(dongle_id: str, alg: str, privada: str, ahora_s: int) -> str:
  import jwt
  tok = jwt.encode({"identity": dongle_id, "orbit": "mqtt", "iat": ahora_s, "exp": ahora_s + TTL_JWT_S},
                   privada, algorithm=alg)
  return tok.decode() if isinstance(tok, bytes) else tok


def _abrir_url(req, timeout):
  return urllib.request.urlopen(req, timeout=timeout, context=contexto_tls())


def _motivo_http(e: urllib.error.HTTPError) -> str:
  try:
    reason = json.loads(e.read() or b"{}").get("reason")
  except Exception:
    reason = None
  if e.code == 401 and reason in ("clock", "signature"):
    return reason
  if e.code == 403 and reason in _CLAVE_RECHAZADA:
    return reason
  return f"http_{e.code}"


def _retry_after(e: urllib.error.HTTPError) -> int:
  """Retry-After en segundos (la forma con fecha se ignora), acotado a RETRY_AFTER_MAX_S."""
  try:
    return max(0, min(RETRY_AFTER_MAX_S, int(str(e.headers.get("Retry-After") or "0").strip())))
  except (AttributeError, TypeError, ValueError):
    return 0


def _pedir(api_base, dongle_id, alg, privada, publica, reintento_auth, abrir=None, ahora_s=None) -> dict:
  tok = jwt_credencial(dongle_id, alg, privada, int(datetime.now(UTC).timestamp()) if ahora_s is None else ahora_s)
  cuerpo = json.dumps({"dongle_id": dongle_id, "pubkey": publica, "key_alg": alg,
                       "reintento_auth": bool(reintento_auth)}).encode()
  req = urllib.request.Request(api_base.rstrip("/") + RUTA_CREDENCIAL, data=cuerpo, method="POST",
                               headers={"Authorization": "JWT " + tok, "Content-Type": "application/json"})
  try:
    with (abrir or _abrir_url)(req, TIMEOUT_HTTPS_S) as r:
      estado = getattr(r, "status", 200)
      data = json.loads(r.read())
  except urllib.error.HTTPError as e:
    raise ErrorCredencial(_motivo_http(e), _retry_after(e)) from e
  except (ssl.SSLError, ssl.CertificateError) as e:
    raise ErrorCredencial("tls") from e
  except urllib.error.URLError as e:
    raise ErrorCredencial("tls" if isinstance(e.reason, ssl.SSLError) else "red") from e
  except (OSError, ValueError) as e:
    raise ErrorCredencial("red") from e
  if not isinstance(data, dict) or not isinstance(data.get("password"), str) or not data["password"]:
    raise ErrorCredencial(f"http_{estado}")
  return data


def pedir_credencial(api_base: str, dongle_id: str, alg: str, privada: str, publica: str,
                     reintento_auth: bool, abrir=None, ahora_s: int | None = None) -> tuple[str, str]:
  """(usuario, contrasena) del broker. Lanza ErrorCredencial."""
  data = _pedir(api_base, dongle_id, alg, privada, publica, reintento_auth, abrir, ahora_s)
  return str(data.get("username") or dongle_id), data["password"]


def _caer_a_legacy(motivo: str, ahora: float) -> None:
  global _legacy_hasta, _motivo_legacy, _fallos, _funnel_desde
  with _lock:
    if _legacy(_config(ahora), motivo) is None:
      return
    _legacy_hasta = ahora + LEGACY_DURANTE_S
    _motivo_legacy = "clave_rechazada" if motivo in _CLAVE_RECHAZADA else "fallos"
    _fallos = 0
    _funnel_desde = None
  cloudlog.warning(f"[ORBIT] funnel no disponible ({motivo}): legacy durante {LEGACY_DURANTE_S} s")


def _aplicar_legacy(activo: bool) -> None:
  """El servidor gobierna legacy.activo (runbook de corte): se persiste si difiere."""
  global _cfg
  with _lock:
    cfg = _config(_reloj_mono())
    actual = cfg.get("legacy").get("activo", True) if isinstance(cfg.get("legacy"), dict) else True
    if bool(actual) == activo:
      return
    if _escribir_config({"legacy": {"activo": activo}}):
      _cfg = None  # se relee ya: destino() lo ve en la siguiente llamada
      cloudlog.warning(f"[ORBIT] el servidor fija legacy.activo = {activo}")


def _credencial(d: Destino, dongle_id: str) -> str:
  global _reintento_auth, _ignorar_rc_auth, _credencial_no_antes
  ahora = _reloj_mono()
  with _lock:
    cache = _credenciales.get((d.host, dongle_id))
    if cache and ahora < cache[1]:
      return cache[0]
  clave = _clave_dispositivo()
  if clave is None:
    raise ErrorCredencial("sin_clave")
  with _lock:
    if ahora < _credencial_no_antes:
      # Aun no toca pedir: el error que nos frena ya se conto (o no cuenta, si fue
      # 429/503). El rc 5 de la contrasena vacia tampoco; el reloj de SIN_CONEXION_S si.
      _ignorar_rc_auth = True
      raise ErrorCredencial("espera")
    _credencial_no_antes = ahora + ESPERA_CREDENCIAL_S
    reintento = _reintento_auth
  alg, privada, publica = clave
  try:
    data = _pedir(f"https://{d.host}", dongle_id, alg, privada, publica, reintento)
  except ErrorCredencial as e:
    with _lock:
      # Se cuenta aqui (o no cuenta): el rc 5 que viene detras no suma otra vez.
      _ignorar_rc_auth = True
      _credencial_no_antes = max(_credencial_no_antes, ahora + e.retry_after)
    if e.motivo in _CLAVE_RECHAZADA:
      _caer_a_legacy(e.motivo, ahora)
    elif e.motivo not in _NO_CUENTAN:
      notificar(d, False)  # red/tls/clock/signature/5xx: fallo de funnel (G4.2 punto 4)
    raise
  try:
    renovar = max(60, int(data.get("renovar_en_s") or RENOVAR_POR_DEFECTO_S))
  except (TypeError, ValueError):
    renovar = RENOVAR_POR_DEFECTO_S
  with _lock:
    _credenciales[(d.host, dongle_id)] = (data["password"], ahora + renovar)
    _reintento_auth = False
  if isinstance(data.get("legacy"), bool):
    _aplicar_legacy(data["legacy"])
  return data["password"]


def _pre_connect_de(d: Destino, dongle_id: str):
  def _pre_connect(client, userdata):
    # Nunca lanza: sin credencial va contrasena vacia, el broker rechaza (rc 5) y cuenta
    # como un fallo normal (o no, si fue 429/503).
    try:
      password = _credencial(d, dongle_id)
    except ErrorCredencial as e:
      cloudlog.warning(f"[ORBIT] sin credencial MQTT ({e.motivo})")
      password = ""
    except Exception:
      cloudlog.exception("[ORBIT] error pidiendo la credencial MQTT")
      password = ""
    try:
      client.username_pw_set(dongle_id, password)
    except Exception:
      cloudlog.exception("[ORBIT] no se pudo fijar la credencial MQTT")
  return _pre_connect


def crear_cliente(d: Destino, dongle_id: str, client_id: str = ""):
  import paho.mqtt.client as mqtt
  if d.enlace != ENLACE_FUNNEL:
    # Exactamente lo de siempre.
    cliente = mqtt.Client()
    cfg = _config(_reloj_mono())
    usuario = (cfg.get("username") or "").strip()
    if usuario:
      cliente.username_pw_set(usuario, cfg.get("password") or None)
    return cliente
  # El broker es compartido con el 1883 anonimo: un client_id igual al dongle permitiria a
  # cualquiera expulsar al coche. Sufijo aleatorio por cada cliente.
  cid = f"{client_id or dongle_id}-{secrets.token_hex(8)}"
  cliente = mqtt.Client(client_id=cid, transport=d.transporte)
  if d.tls:
    cliente.tls_set_context(contexto_tls())
  if d.transporte == "websockets":
    cliente.ws_set_options(path=d.path)
  cliente.on_pre_connect = _pre_connect_de(d, dongle_id)
  return cliente


def _sin_conexion_demasiado(ahora: float) -> bool:
  """Con _lock cogido: apunta el primer fallo y dice si ya van SIN_CONEXION_S sin un rc 0."""
  global _funnel_desde
  if _funnel_desde is None:
    _funnel_desde = ahora
  return ahora - _funnel_desde >= SIN_CONEXION_S


def desconectado(d: Destino | None, rc: int | None = None) -> None:
  """on_disconnect con rc != 0. No cuenta como fallo (paho lo llama tambien tras un rc 5
  y tras perder una conexion buena), pero un cierre antes del CONNACK solo llega por aqui:
  alimenta el reloj de SIN_CONEXION_S."""
  if d is None or d.enlace != ENLACE_FUNNEL or rc == 0:
    return
  ahora = _reloj_mono()
  with _lock:
    caer = _sin_conexion_demasiado(ahora)
  if caer:
    _caer_a_legacy("sin_connack", ahora)


def notificar(d: Destino | None, ok: bool, rc: int | None = None) -> None:
  """Resultado de una conexion: on_connect (rc), on_connect_fail o excepcion de connect()."""
  global _enlace, _fallos, _reintento_auth, _ignorar_rc_auth, _funnel_desde
  if d is None:
    return
  ahora = _reloj_mono()
  with _lock:
    if ok:
      _enlace = d.enlace
      if d.enlace == ENLACE_FUNNEL:
        _fallos = 0
        _funnel_desde = None
    if d.enlace != ENLACE_FUNNEL:
      return
    if not ok:
      if rc in (4, 5):
        for k in [k for k in _credenciales if k[0] == d.host]:
          del _credenciales[k]
        _reintento_auth = True
      # El reloj corre aunque este fallo no cuente (429/503, rc 5 de una espera).
      if _sin_conexion_demasiado(ahora):
        motivo = "sin_connack"
      elif rc in (4, 5) and _ignorar_rc_auth:
        _ignorar_rc_auth = False
        return
      else:
        _fallos += 1
        if _fallos < FALLOS_PARA_LEGACY:
          return
        motivo = "fallos"
  if ok:
    if not funnel_ok():
      try:
        with open(RUTA_FUNNEL_OK, "w"):
          pass
      except OSError:
        pass  # PC sin /data
    return
  _caer_a_legacy(motivo, ahora)
