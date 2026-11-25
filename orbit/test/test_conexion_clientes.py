"""Los tres clientes MQTT del firmware sobre la factoria conexion_mqtt (contrato global G4.3).

Lo que fijan estos tests (paho falso, conexion_mqtt real con config en tmp):

    Factoria ............. en funnel, telemetria, mando y events_mqtt crean el cliente con
                           conexion_mqtt.crear_cliente y conectan a servidor.host:8443; sin
                           servidor.host, mqtt.Client() y el broker de siempre.
    Fallos ............... connect() que lanza, on_connect rc != 0 y on_connect_fail cuentan:
                           3 en funnel -> destino() legacy.
    Caps ................. llevan "link" (funnel | legacy).
    */global ............. la purga de retenidos solo por legacy.
    Conmutacion .......... funnel -> legacy crea cliente NUEVO y el CameraSender publica por el;
                           el viejo no recibe nada. Entre dos legacy no se conmuta.
    Sin ordenes .......... con funnel_ok() y enlace legacy, mando no se suscribe a
                           orbit/v2/cmd/<d> ni a telemetry_config/<d>/left.
    events_mqtt .......... reinicia al cambiar el destino; la llamada RT no pide credencial.
"""
import json
import threading
from types import SimpleNamespace

import paho.mqtt.client as paho
import pytest

from openpilot.orbit import camera_sender as cs
from openpilot.orbit import config_broker as cb
from openpilot.orbit import conexion_mqtt as cm
from openpilot.orbit import events_mqtt as ev
from openpilot.orbit import mqtt_comandos as mc
from openpilot.orbit import mqtt_envio_general as meg
from openpilot.orbit.command_spec import TOPIC_CAPS
from openpilot.orbit.test.test_mando_v1_por_router import DONGLE, _comandos as _comandos_router

HOST = "coche.tail0.ts.net"
BROKER = "83.61.25.38"


class ClientePaho:
  """paho.mqtt.client.Client falso: apunta todo lo que se le hace, sin red."""
  creados: list = []

  def __init__(self, client_id="", transport="tcp", **_kw):
    self.client_id, self.transport = client_id, transport
    self.tls = None
    self.ws_path = None
    self.on_pre_connect = None
    self.on_connect = self.on_connect_fail = self.on_disconnect = self.on_message = None
    self.credenciales = []
    self.connects = []
    self.publicados = []
    self.subs = []
    self.parado = self.desconectado = False
    self.falla_connect = False
    ClientePaho.creados.append(self)

  def tls_set_context(self, ctx):
    self.tls = ctx

  def ws_set_options(self, path="/mqtt", headers=None):
    self.ws_path = path

  def username_pw_set(self, u, p=None):
    self.credenciales.append((u, p))

  def max_queued_messages_set(self, n): pass
  def reconnect_delay_set(self, **kw): pass
  def will_set(self, *a, **kw): pass

  def connect(self, host, port, keepalive=60):
    self.connects.append((host, port))
    if self.falla_connect:
      raise OSError("sin ruta")

  def connect_async(self, host, port, keepalive=60):
    self.connects.append((host, port))

  def loop_start(self): pass

  def loop_stop(self):
    self.parado = True

  def disconnect(self):
    self.desconectado = True

  def is_connected(self):
    return True

  def subscribe(self, topic, qos=0):
    self.subs.append(topic)

  def publish(self, topic, payload=None, qos=0, retain=False):
    self.publicados.append((topic, payload, qos, retain))
    return SimpleNamespace(rc=paho.MQTT_ERR_SUCCESS)


@pytest.fixture
def entorno(tmp_path, monkeypatch):
  """Config real en tmp (via config_broker), reloj valido y clave de dispositivo: funnel."""
  plantilla = tmp_path / "config_mqtt.json"
  datos = tmp_path / "data"
  datos.mkdir()
  monkeypatch.setattr(cb, "RUTA_PLANTILLA", str(plantilla))
  monkeypatch.setattr(cb, "DIR_PERSISTENTE", str(datos))
  monkeypatch.setattr(cb, "RUTA_PERSISTENTE", str(datos / "orbit_config_mqtt.json"))
  monkeypatch.setattr(cb, "_migracion_hecha", True)
  monkeypatch.setattr(cm, "_leer_config", cb.leer_config)  # sin el aislamiento del conftest
  monkeypatch.setattr(cm, "get_key_pair", lambda: ("ES256", "priv", "pub"))
  monkeypatch.setattr(cm, "reloj_valido", lambda: True)
  monkeypatch.setattr(cm, "_pedir", lambda *a, **k: pytest.fail("credencial pedida fuera del hilo de red"))
  monkeypatch.setattr(paho, "Client", ClientePaho)
  ClientePaho.creados = []

  def config(host=HOST, legacy=True):
    plantilla.write_text(json.dumps({"broker": BROKER, "broker_port": 1883, "username": "", "password": "",
                                     "servidor": {"host": host, "transporte": "mqtts", "puerto": 8443, "tls": True},
                                     "legacy": {"activo": legacy}}))
    cm.reiniciar_estado()

  config()
  return config


def _envio():
  e = meg.MQTTEnvioGeneral.__new__(meg.MQTTEnvioGeneral)
  e.DongleID, e.dongle_valido, e.conectado = DONGLE, True, False
  e.broker_address, e.broker_port = BROKER, 1883
  e.mqtt_username = e.mqtt_password = None
  e.stop_event = threading.Event()
  e._conn_stop = threading.Event()
  e._relanzar_hilo_conexion = lambda: None
  e.camera_sender = None
  e.comandos_mqtt = None
  return e


def _comandos():
  c = mc.MQTTComandos.__new__(mc.MQTTComandos)
  c.DongleID, c.dongle_valido, c.conectado = DONGLE, True, False
  c.broker_address, c.broker_port = BROKER, 1883
  c.mqtt_username = c.mqtt_password = None
  c.stop_event = threading.Event()
  c._conn_stop = threading.Event()
  c._conn_lock = threading.Lock()
  c._relanzar_hilo_conexion = lambda: None
  return c


class _StopTras:
  """Event de relevo: wait() devuelve True a la vuelta k (sin dormir)."""

  def __init__(self, k):
    self.k, self.n = k, 0

  def is_set(self):
    return self.n >= self.k

  def wait(self, timeout=None):
    self.n += 1
    return self.is_set()


# ---------------------------------------------------------------------------- factoria

@pytest.mark.parametrize("fabrica", [_envio, _comandos], ids=["telemetria", "mando"])
def test_en_funnel_usan_la_factoria_y_conectan_al_servidor(entorno, fabrica):
  obj = fabrica()
  obj.init_mqtt()
  cli = obj.mqttc
  assert obj._destino.enlace == "funnel"
  assert cli.tls is not None and cli.on_pre_connect is not None, "cliente de crear_cliente (TLS + credencial)"
  assert cli.client_id != DONGLE and cli.client_id.startswith(DONGLE)
  assert cli.on_connect_fail is not None
  obj.setup_mqtt(_StopTras(1))
  assert cli.connects == [(HOST, 8443)]


@pytest.mark.parametrize("fabrica", [_envio, _comandos], ids=["telemetria", "mando"])
def test_sin_host_cliente_y_broker_de_siempre(entorno, fabrica):
  entorno(host="")
  obj = fabrica()
  obj.init_mqtt()
  cli = obj.mqttc
  assert obj._destino.enlace == "legacy"
  assert (cli.client_id, cli.transport, cli.tls, cli.on_pre_connect, cli.credenciales) == ("", "tcp", None, None, [])
  obj.setup_mqtt(_StopTras(1))
  assert cli.connects == [(BROKER, 1883)]


@pytest.mark.parametrize("fabrica", [_envio, _comandos], ids=["telemetria", "mando"])
def test_tres_connect_fallidos_en_funnel_llevan_a_legacy(entorno, fabrica):
  obj = fabrica()
  obj.init_mqtt()
  obj.mqttc.falla_connect = True
  obj.setup_mqtt(_StopTras(3))
  assert len(obj.mqttc.connects) == 3
  assert cm.destino().enlace == "legacy"


@pytest.mark.parametrize("fabrica", [_envio, _comandos], ids=["telemetria", "mando"])
def test_on_connect_fail_y_rc_cuentan_como_fallo(entorno, fabrica):
  obj = fabrica()
  obj.params = SimpleNamespace(put_bool=lambda *a: None)
  obj.init_mqtt()
  obj.on_connect_fail(obj.mqttc, None)
  obj.on_connect_fail(obj.mqttc, None)
  assert cm.destino().enlace == "funnel"
  obj.on_connect(obj.mqttc, None, None, 3)
  assert cm.destino().enlace == "legacy"


# --------------------------------------------------------------------------------- caps

@pytest.mark.parametrize("enlace", ["funnel", "legacy"])
def test_caps_llevan_link(monkeypatch, enlace):
  monkeypatch.setattr(mc, "get_key_pair", lambda: (None, None, None))
  c = _comandos_router()
  c._destino = cm.Destino(enlace, "h", 1, "tcp", False, "")
  assert c.maybe_publish_caps(forzar=True)
  caps = json.loads([p for t, p, *_ in c.mqttc.publicados if t == TOPIC_CAPS.format(DONGLE)][-1])
  assert caps["link"] == enlace


def test_cambiar_de_link_republica_las_caps(monkeypatch):
  monkeypatch.setattr(mc, "get_key_pair", lambda: (None, None, None))
  c = _comandos_router()
  c._destino = cm.Destino("legacy", "h", 1, "tcp", False, "")
  assert c.maybe_publish_caps(forzar=True)
  assert not c.maybe_publish_caps()
  c._destino = cm.Destino("funnel", "h", 8443, "tcp", True, "")
  assert c.maybe_publish_caps()


# ------------------------------------------------------------------------- purga global

class _Params:
  def __init__(self):
    self.valores = {}

  def get(self, k, *a, **kw):
    return self.valores.get(k)

  def put(self, k, v):
    self.valores[k] = v


@pytest.mark.parametrize("enlace, purga", [("funnel", False), ("legacy", True)])
def test_purga_de_global_solo_por_legacy(enlace, purga):
  e = _envio()
  e.params = _Params()
  e.mqttc = ClientePaho()
  e._destino = cm.Destino(enlace, "h", 1, "tcp", False, "")
  e._purge_retenidos_legacy()
  globales = [t for t, *_ in e.mqttc.publicados if t.endswith("/global")]
  assert bool(globales) is purga


# ---------------------------------------------------------------------------- conmutacion

def _camara(cliente):
  cam = cs.CameraSender.__new__(cs.CameraSender)
  cam.mqtt_client, cam.dongle_id, cam.camera_type = cliente, DONGLE, "road"
  cam.frame_count = cam.error_count = cam.consecutive_errors = 0
  cam._log_debug = lambda *a, **k: None
  return cam


def test_funnel_a_legacy_cliente_nuevo_y_la_camara_lo_usa(entorno):
  e = _envio()
  e.init_mqtt()
  viejo = e.mqttc
  e.camera_sender = _camara(viejo)
  comandos = _comandos()
  comandos.init_mqtt()
  e.comandos_mqtt = comandos
  cmd_viejo = comandos.mqttc

  entorno(host="")          # el destino pasa a legacy
  e._destino_t = float("-inf")
  e._maybe_cambiar_destino()

  assert e.mqttc is not viejo and e._destino.enlace == "legacy"
  assert viejo.parado and viejo.desconectado
  assert comandos.mqttc is not cmd_viejo and cmd_viejo.desconectado
  assert e.camera_sender.send_image(b"\xff\xd8", 1, 0)
  assert [t for t, *_ in e.mqttc.publicados] == [f"telemetry_mqtt/{DONGLE}/camera/road"]
  assert viejo.publicados == []


def test_entre_dos_legacy_no_se_conmuta(entorno):
  entorno(host="")
  e = _envio()
  e.init_mqtt()
  cli = e.mqttc
  e._destino = cm.Destino("legacy", "otro", 1883, "tcp", False, "")
  e._destino_t = float("-inf")
  e._maybe_cambiar_destino()
  assert e.mqttc is cli, "entre legacy manda _maybe_reload_broker, como siempre"


# --------------------------------------------------------------------------- sin ordenes

def _suscripciones(destino, funnel_ok, monkeypatch, tmp_path):
  ruta = tmp_path / "orbit_funnel_ok"
  if funnel_ok:
    ruta.write_text("")
  monkeypatch.setattr(cm, "RUTA_FUNNEL_OK", str(ruta))
  c = _comandos()
  c.router = SimpleNamespace(topic_cmd=f"orbit/v2/cmd/{DONGLE}")
  c._refrescar_dongle = lambda: None
  c.maybe_publish_caps = lambda **k: None
  c._destino = destino
  cli = ClientePaho()
  c._on_connect(cli, None, None, 0)
  return cli.subs


LEGACY = cm.Destino("legacy", BROKER, 1883, "tcp", False, "")
FUNNEL = cm.Destino("funnel", HOST, 8443, "tcp", True, "")


def test_legacy_tras_funnel_sin_ordenes(monkeypatch, tmp_path):
  subs = _suscripciones(LEGACY, True, monkeypatch, tmp_path)
  for prohibido in (f"orbit/v2/cmd/{DONGLE}", f"telemetry_config/{DONGLE}/left",
                    f"telemetry_config/{DONGLE}/brutebreak", f"orbit/v2/cfg/desired/{DONGLE}",
                    f"orbit/v2/dev/{DONGLE}/roundabout"):
    assert prohibido not in subs
  assert f"telemetry_config/{DONGLE}/steer_torque_mode" not in subs   # estado, no orden
  assert f"telemetry_config/{DONGLE}/healthcheck" in subs
  for identidad in ("enroll_ack", "unlink_ack"):   # identidad: solo por Funnel
    assert f"telemetry_config/{DONGLE}/{identidad}" not in subs


@pytest.mark.parametrize("destino, funnel_ok", [(LEGACY, False), (FUNNEL, True)], ids=["legacy-sin-funnel", "funnel"])
def test_con_ordenes_si_no_hay_riesgo(monkeypatch, tmp_path, destino, funnel_ok):
  subs = _suscripciones(destino, funnel_ok, monkeypatch, tmp_path)
  assert f"orbit/v2/cmd/{DONGLE}" in subs and f"telemetry_config/{DONGLE}/left" in subs
  assert f"telemetry_config/{DONGLE}/steer_torque_mode" not in subs   # estado, no orden


def _despacho(destino, funnel_ok, monkeypatch, tmp_path):
  """on_message con espias en cada salida: devuelve f(topic) -> lista de salidas tocadas."""
  ruta = tmp_path / "orbit_funnel_ok"
  if funnel_ok:
    ruta.write_text("")
  monkeypatch.setattr(cm, "RUTA_FUNNEL_OK", str(ruta))
  tocado = []
  monkeypatch.setattr(mc.cfg2, "get_bus", lambda: SimpleNamespace(recibir=lambda p: tocado.append("cfg")))
  c = _comandos()
  c._destino = destino
  c.params = SimpleNamespace(put_bool=lambda k, v: tocado.append(k), get_bool=lambda k: False)
  c.save_debug_message = lambda t, p: None
  c.router = SimpleNamespace(on_message=lambda *a: tocado.append("v2"))
  c._v1_al_router = lambda *a: tocado.append("v1")
  c._camera_config_con_interruptor = lambda p: tocado.append("camara")
  c.handle_enroll_ack = lambda p: tocado.append("enroll_ack")

  def enviar(topic, payload=b'{"a": 1}'):
    tocado.clear()
    c.on_message(None, None, SimpleNamespace(topic=topic, payload=payload, retain=False))
    return list(tocado)
  return enviar


ORDENES_NO_SUSCRITAS = [f"orbit/v2/cmd/{DONGLE}", f"telemetry_config/{DONGLE}/left",
                        f"telemetry_config/{DONGLE}/brutebreak", f"orbit/v2/cfg/desired/{DONGLE}",
                        f"orbit/v2/dev/{DONGLE}/roundabout", f"telemetry_config/{DONGLE}/camera_config"]


def test_legacy_tras_funnel_on_message_descarta_lo_no_suscrito(monkeypatch, tmp_path):
  # Un broker hostil puede publicar en topics no suscritos y paho los entrega a on_message.
  enviar = _despacho(LEGACY, True, monkeypatch, tmp_path)
  for topic in ORDENES_NO_SUSCRITAS:
    assert enviar(topic, b"1" if topic.endswith("roundabout") else b'{"a": 1}') == [], topic
  assert enviar(f"telemetry_config/{DONGLE}/enroll_ack") == []
  assert enviar(f"telemetry_config/{DONGLE}/healthcheck") == ["v1"]


class _ParamsEspia:
  """Params en memoria que apunta cada escritura."""

  def __init__(self, **iniciales):
    self.d, self.escrituras = dict(iniciales), []

  def get(self, k):
    return self.d.get(k)

  def get_bool(self, k):
    return bool(self.d.get(k))

  def put(self, k, v):
    self.escrituras.append(k)
    self.d[k] = v

  put_bool = put

  def remove(self, k):
    self.escrituras.append(k)
    self.d.pop(k, None)


@pytest.mark.parametrize("topic, payload", [
  ("enroll_ack", b'{"claimed": false, "ts": 1}'),
  ("enroll_ack", b'{"claimed": true, "user_name": "intruso", "ts": 1}'),
  ("unlink_ack", b'{"ok": true, "ts": 1}'),
  ("unlink_ack", b'{"ok": false, "reason": "x", "ts": 1}'),
])
@pytest.mark.parametrize("destino, funnel_ok, cambia", [(LEGACY, True, False), (LEGACY, False, True), (FUNNEL, True, True)],
                         ids=["sin-ordenes", "legacy-sin-funnel", "funnel"])
def test_identidad_solo_fuera_de_sin_ordenes(monkeypatch, tmp_path, topic, payload, destino, funnel_ok, cambia):
  ruta = tmp_path / "orbit_funnel_ok"
  if funnel_ok:
    ruta.write_text("")
  monkeypatch.setattr(cm, "RUTA_FUNNEL_OK", str(ruta))
  c = _comandos()
  c._destino = destino
  c.params = _ParamsEspia(OrbitClaimed=True, OrbitOwner="dueno", OrbitOwnerRole="user",
                          OrbitUnlinkNonce="n1", OrbitUnlinkRequest=True)
  antes = dict(c.params.d)
  c.save_debug_message = lambda t, p: None
  c.on_message(None, None, SimpleNamespace(topic=f"telemetry_config/{DONGLE}/{topic}", payload=payload, retain=False))
  if cambia:
    assert c.params.escrituras
  else:
    assert c.params.escrituras == [] and c.params.d == antes


def test_por_funnel_on_message_despacha_las_ordenes(monkeypatch, tmp_path):
  enviar = _despacho(FUNNEL, True, monkeypatch, tmp_path)
  assert enviar(f"orbit/v2/cmd/{DONGLE}") == ["v2"]
  assert enviar(f"telemetry_config/{DONGLE}/left") == ["v1"]
  assert enviar(f"orbit/v2/cfg/desired/{DONGLE}") == ["cfg"]
  assert enviar(f"telemetry_config/{DONGLE}/camera_config") == ["camara"]


@pytest.mark.parametrize("fabrica", [_envio, _comandos], ids=["telemetria", "mando"])
def test_on_disconnect_sin_connack_acaba_en_legacy(entorno, fabrica):
  # Broker que acepta TLS y cierra antes del CONNACK: paho solo llama a on_disconnect.
  obj = fabrica()
  obj.params = SimpleNamespace(put_bool=lambda *a: None)
  obj._destino = cm.destino()
  t = [1000.0]
  cm._reloj_mono, orig = (lambda: t[0]), cm._reloj_mono
  try:
    for _ in range(int(cm.SIN_CONEXION_S // 30)):
      obj.on_disconnect(None, None, 7)
      assert cm.destino(t[0]).enlace == "funnel"
      t[0] += 30
    obj.on_disconnect(None, None, 7)
    assert cm.destino(t[0]).enlace == "legacy"
  finally:
    cm._reloj_mono = orig


# ---------------------------------------------------------------------------- events_mqtt

@pytest.fixture
def eventos(entorno, monkeypatch):
  monkeypatch.setattr(ev, "_mqtt_client", None)
  monkeypatch.setattr(ev, "_mqtt_destino", None)
  monkeypatch.setattr(ev, "_mqtt_connected", False)
  monkeypatch.setattr(ev, "_broker_cfg_cache_ts", float("-inf"))
  monkeypatch.setattr(ev, "_destino_cache_ts", float("-inf"))
  monkeypatch.setattr(ev, "_dongle_id_cache", DONGLE)
  return entorno


def _expirar_caches(monkeypatch):
  monkeypatch.setattr(ev, "_broker_cfg_cache_ts", float("-inf"))
  monkeypatch.setattr(ev, "_destino_cache_ts", float("-inf"))


def _esperar_cierres():
  for h in threading.enumerate():
    if h.name == "orbit-events-cierre":
      h.join(timeout=5)


def test_events_el_cierre_del_viejo_no_bloquea_el_hilo_rt(eventos, monkeypatch):
  # loop_stop() hace join sin timeout del hilo de paho, que puede estar en el HTTPS de la
  # credencial: el hilo de 100 Hz de selfdrived no puede esperarlo.
  funnel = ev._ensure_mqtt_client()
  suelta = threading.Event()
  funnel.loop_stop = lambda: suelta.wait(10)
  eventos(host="")
  _expirar_caches(monkeypatch)
  try:
    legacy = ev._ensure_mqtt_client()
    assert legacy is not funnel and not suelta.is_set()
    assert funnel.on_disconnect is None and funnel.on_connect is None, "el viejo ya no toca el estado"
  finally:
    suelta.set()
    _esperar_cierres()
  assert funnel.desconectado


def test_events_funnel_por_la_factoria_sin_red_en_la_llamada(eventos):
  cli = ev._ensure_mqtt_client()
  assert cli.tls is not None and cli.on_pre_connect is not None
  assert cli.on_connect_fail is not None
  assert cli.connects == [(HOST, 8443)]   # connect_async: la credencial la pide el hilo de red


def test_events_reinicia_al_cambiar_el_destino(eventos, monkeypatch):
  funnel = ev._ensure_mqtt_client()
  assert ev._ensure_mqtt_client() is funnel
  eventos(host="")
  _expirar_caches(monkeypatch)
  legacy = ev._ensure_mqtt_client()
  _esperar_cierres()
  assert legacy is not funnel and funnel.parado and funnel.desconectado
  assert legacy.connects == [(BROKER, 1883)] and legacy.tls is None


def test_events_tres_fallos_llevan_a_legacy(eventos):
  cli = ev._ensure_mqtt_client()
  cli.on_connect_fail(cli, None)
  cli.on_connect(cli, None, None, 5)
  cli.on_connect_fail(cli, None)
  assert cm.destino().enlace == "legacy"
