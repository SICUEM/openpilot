# log_mqtt.py
import json
from datetime import datetime
from openpilot.common.params import Params
import os
import importlib.util

#import sys
import subprocess
import socket
import threading

PERSIST_PATH = "/data/pythonpath"
#sys.path.append(PERSIST_PATH)

LIB_NAME = "paho"
PACKAGE_NAME = "paho-mqtt"

# ← Variable centinela (cache)
PAHO_AVAILABLE = None
INSTALL_THREAD_LAUNCHED = False

def is_library_installed_cached():
    global PAHO_AVAILABLE
    # Si ya lo sabemos → evitar trabajo extra
    if PAHO_AVAILABLE is not None:
        return PAHO_AVAILABLE
    # Comprobación real (solo la primera vez)
    PAHO_AVAILABLE = importlib.util.find_spec(LIB_NAME) is not None
    return PAHO_AVAILABLE

def have_internet(host="8.8.8.8", port=53, timeout=2):
    try:
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False

def install_library_threaded(package_name, target_dir):
    global PAHO_AVAILABLE
    try:
        subprocess.check_call(["pip", "install", package_name, "-t", target_dir])
        # Actualizamos la cache
        PAHO_AVAILABLE = importlib.util.find_spec(LIB_NAME) is not None
    except Exception as e:
        print(f"[MQTT] Error instalando: {e}")

def launch_install_thread():
    global INSTALL_THREAD_LAUNCHED
    if INSTALL_THREAD_LAUNCHED:
        return  # Evitar lanzar múltiples hilos
    INSTALL_THREAD_LAUNCHED = True
    t = threading.Thread(target=install_library_threaded, args=(PACKAGE_NAME, PERSIST_PATH), daemon=True)
    t.start()
    INSTALL_THREAD_LAUNCHED = False

def test_and_set_paho_async():
    global PAHO_AVAILABLE
    # 1. ¿Librería ya disponible? (cacheado)
    if is_library_installed_cached():
        return True
    # 2. No instalada, ¿hay Internet?
    if not have_internet():
        return False
    # 3. Lanzamos instalación en hilo (solo una vez)
    launch_install_thread()
    return False

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
    if not test_and_set_paho_async():
        return
    a = 1
    '''
    topic = f"telemetry_mqtt/{DONGLE_ID}/logs"
    payload = {
        "log": mensaje,
        "level": nivel,
        "timestamp": datetime.now().isoformat(),
        "origen": origen
    }
    publish.single(topic, json.dumps(payload), hostname=BROKER, port=PORT)
    '''

def enviar_log_test(dongle_id_manual, mensaje, nivel="INFO", origen="desconocido"):
    if not test_and_set_paho_async():
        return
    a = 1
    '''
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


'''
COMO USARLO

from log_mqtt import enviar_log

enviar_log("Se activó el freno por seguridad", nivel="WARNING", origen="carControl")




COMO USAR TEST

from log_mqtt import enviar_log_test

enviar_log_test("DongleFake123", "Esto es un log de prueba", nivel="DEBUG", origen="test_script")


'''
