# log_mqtt.py
import json
from datetime import datetime
from openpilot.common.params import Params
import os
import importlib.util

if importlib.util.find_spec("paho.mqtt"):
    import paho.mqtt.publish as publish

# Obtener ruta base
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_PATH, "config_mqtt.json")

# Cargar configuración MQTT
with open(CONFIG_FILE, "r") as f:
    config = json.load(f)
    BROKER = config.get("broker", "localhost")
    PORT = config.get("broker_port", 1883)

# Obtener DongleID automáticamente
params = Params()
DONGLE_ID = params.get("DongleId").decode("utf-8") if params.get("DongleId") else "UnregisteredDevice"

def enviar_log(mensaje, nivel="INFO", origen="desconocido"):
    topic = f"telemetry_mqtt/{DONGLE_ID}/logs"
    payload = {
        "log": mensaje,
        "level": nivel,
        "timestamp": datetime.now().isoformat(),
        "origen": origen
    }
    publish.single(topic, json.dumps(payload), hostname=BROKER, port=PORT)
  
def enviar_log_test(dongle_id_manual, mensaje, nivel="INFO", origen="desconocido"):
    topic = f"telemetry_mqtt/{dongle_id_manual}/logs"
    payload = {
        "log": mensaje,
        "level": nivel,
        "timestamp": datetime.now().isoformat(),
        "origen": origen
    }
    publish.single(topic, json.dumps(payload), hostname=BROKER, port=PORT)
    #print(f"📤 Log de test enviado a {topic}")


'''
COMO USARLO

from log_mqtt import enviar_log

enviar_log("Se activó el freno por seguridad", nivel="WARNING", origen="carControl")




COMO USAR TEST

from log_mqtt import enviar_log_test

enviar_log_test("DongleFake123", "Esto es un log de prueba", nivel="DEBUG", origen="test_script")


'''
