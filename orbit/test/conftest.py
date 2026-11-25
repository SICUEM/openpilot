"""Aislamiento de conexion_mqtt para TODOS los tests de orbit/test (contrato global G4.8).

La plantilla versionada (orbit/config_mqtt.json) lleva servidor.host y la maquina de
desarrollo puede tener ~/.comma/persist/comma/id_ecdsa: sin esto un test viejo que
construya un cliente MQTT iria por funnel e intentaria HTTPS de verdad. Aqui se fija
"sin clave" y servidor.host vacio, es decir, el camino legacy de siempre.

Un fichero que pruebe la factoria de verdad lo anula definiendo su propio fixture
`aislar_conexion_mqtt` (pytest da prioridad al del modulo).
"""
import pytest

from openpilot.orbit import conexion_mqtt as cm


@pytest.fixture(autouse=True)
def aislar_conexion_mqtt(monkeypatch, tmp_path):
  leer = cm._leer_config

  def sin_servidor():
    cfg = dict(leer())
    servidor = cfg.get("servidor") if isinstance(cfg.get("servidor"), dict) else {}
    cfg["servidor"] = {**servidor, "host": ""}
    return cfg

  monkeypatch.setattr(cm, "_leer_config", sin_servidor)
  monkeypatch.setattr(cm, "get_key_pair", lambda: (None, None, None))
  monkeypatch.setattr(cm, "RUTA_FUNNEL_OK", str(tmp_path / "orbit_funnel_ok"))
  cm.reiniciar_estado()
  yield
  cm.reiniciar_estado()
