"""Senal de prueba de rotonda (orbit/v2/dev/<dongle>/roundabout): solo escribe un param."""
from types import SimpleNamespace

from openpilot.orbit import config_v2 as cfg2
from openpilot.orbit.mqtt_comandos import MQTTComandos

DONGLE = "0123456789abcdef"
TOPIC = cfg2.TOPIC_DEV_ROUNDABOUT.format(DONGLE)


class _Params:
  def __init__(self):
    self.valores = {}

  def put_bool(self, key, value):
    self.valores[key] = bool(value)

  def get(self, key, *args, **kwargs):
    return self.valores.get(key)


def _comandos():
  c = MQTTComandos.__new__(MQTTComandos)
  c.params = _Params()
  c.DongleID = DONGLE
  c.dongle_valido = True
  c.router = None
  c.save_debug_message = lambda *a, **k: None
  c._refrescar_dongle = lambda: None
  c.maybe_publish_caps = lambda **k: None
  return c


def _enviar(c, payload):
  c.on_message(None, None, SimpleNamespace(topic=TOPIC, payload=payload.encode(), retain=False))


def test_uno_pone_el_param_a_true():
  c = _comandos()
  _enviar(c, "1")
  assert c.params.valores["OrbitDevRoundabout"] is True


def test_cero_lo_pone_a_false():
  c = _comandos()
  _enviar(c, "1")
  _enviar(c, "0")
  assert c.params.valores["OrbitDevRoundabout"] is False


def test_payload_basura_no_lo_cambia():
  c = _comandos()
  _enviar(c, "1")
  for basura in ("", "2", "true", "{}"):
    _enviar(c, basura)
  assert c.params.valores["OrbitDevRoundabout"] is True


def test_on_connect_se_suscribe_con_el_dongle():
  c = _comandos()
  subs = []
  cliente = SimpleNamespace(subscribe=lambda topic, qos=0: subs.append((topic, qos)))
  c._on_connect(cliente, None, None, 0)
  assert (f"orbit/v2/dev/{DONGLE}/roundabout", 1) in subs
