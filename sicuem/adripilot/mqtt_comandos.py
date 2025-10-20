#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import time
import threading
import paho.mqtt.client as mqtt
from openpilot.common.params import Params
import os

class MQTTComandos:
  def __init__(self):
    self.base_path = os.path.dirname(os.path.abspath(__file__))
    self.jsonConfig = os.path.join(self.base_path, "config_mqtt.json")
    self.params = Params()
    self.DongleID = self.params.get("DongleId").decode("utf-8") if self.params.get("DongleId") else "DongleID"
    self.conectado = False
    self.stop_event = threading.Event()
    self.load_config()
    self.init_mqtt()

  def load_config(self):
    with open(self.jsonConfig, "r") as f:
      config = json.load(f)
      self.broker_address = config.get("broker", "localhost")

  def init_mqtt(self):
    self.mqttc = mqtt.Client()
    self.mqttc.on_connect = self.on_connect
    self.mqttc.on_disconnect = self.on_disconnect
    self.mqttc.on_message = self.on_message
    self.mqttc.reconnect_delay_set(min_delay=1, max_delay=30)
    threading.Thread(target=self.setup_mqtt, daemon=True).start()

  def setup_mqtt(self):
    while not self.stop_event.is_set():
      try:
        self.mqttc.connect(self.broker_address, 1883, 60)
        if not self.conectado:
          self.mqttc.loop_start()
          self.conectado = True
          print("✅ MQTT Comandos conectado al broker")
        break
      except Exception as e:
        print(f"❌ Error al conectar MQTT Comandos: {e}")
        time.sleep(5)

  def on_connect(self, client, userdata, flags, rc):
    if rc == 0:
      self.conectado = True
      print("🔌 MQTT Comandos conectado")
      # Suscribirse a los comandos de cambio de carril
      client.subscribe(f"telemetry_config/{self.DongleID}/left", qos=0)
      client.subscribe(f"telemetry_config/{self.DongleID}/right", qos=0)
      client.subscribe(f"telemetry_config/{self.DongleID}/intervalos", qos=0)
      print(f"📡 Suscrito a comandos para {self.DongleID}")
      print(f"📡 Topics suscritos:")
      print(f"   - telemetry_config/{self.DongleID}/left")
      print(f"   - telemetry_config/{self.DongleID}/right")
      print(f"   - telemetry_config/{self.DongleID}/intervalos")
    else:
      print(f"🔌 Error conexión MQTT Comandos: {rc}")

  def on_disconnect(self, client, userdata, rc):
    self.conectado = False
    print("🔌 MQTT Comandos desconectado. Reintentando...")

  def on_message(self, client, userdata, msg):
    """Callback que maneja los mensajes MQTT de comandos."""
    try:
      topic = msg.topic
      payload = msg.payload.decode(errors="ignore").strip().lower()

      print(f"📥 MQTT recibido: {topic} -> {payload}")

      # Comando de cambio de carril a la izquierda
      if topic.endswith("/left"):
        self.handle_lane_change_left(payload)

      # Comando de cambio de carril a la derecha
      elif topic.endswith("/right"):
        self.handle_lane_change_right(payload)

      # Comando de intervalos
      elif topic.endswith("/intervalos"):
        self.handle_intervalos(payload)

    except Exception as e:
      print(f"❌ Error procesando comando MQTT: {e}")

  def handle_lane_change_left(self, payload):
    """Maneja el comando de cambio de carril a la izquierda."""
    print(f"🚗 Procesando comando cambio carril IZQUIERDA para {self.DongleID}")

    # Verificar toggle de seguridad c_carril
    if not self.params.get_bool("c_carril"):
      print("🛑 Cambio de carril a IZQUIERDA bloqueado por toggle c_carril.")
      return

    if payload == "false":
      self.params.put_bool("ForceLaneChangeLeft", False)
      self.params.put_bool("ForceLaneChangeRight", False)
      print(f"🛑 Cambio de carril cancelado (left=false) para {self.DongleID}")

    elif self.params.get_bool("ForceLaneChangeRight"):
      print("⚠️ No se puede activar IZQ, ya hay cambio a DERECHA")
      self.params.put_bool("ForceLaneChangeLeft", False)
      self.params.put_bool("ForceLaneChangeRight", False)
      print(f"🛑 Ambos cancelados por conflicto IZQ-DER")
    else:
      self.params.put_bool("ForceLaneChangeLeft", True)
      print(f"✅ Ejecutando cambio de carril IZQUIERDA para {self.DongleID}")

  def handle_lane_change_right(self, payload):
    """Maneja el comando de cambio de carril a la derecha."""
    print(f"🚗 Procesando comando cambio carril DERECHA para {self.DongleID}")

    # Verificar toggle de seguridad c_carril
    if not self.params.get_bool("c_carril"):
      print("🛑 Cambio de carril a DERECHA bloqueado por toggle c_carril.")
      return

    if payload == "false":
      self.params.put_bool("ForceLaneChangeLeft", False)
      self.params.put_bool("ForceLaneChangeRight", False)
      print(f"🛑 Cambio de carril cancelado (right=false) para {self.DongleID}")

    elif self.params.get_bool("ForceLaneChangeLeft"):
      print("⚠️ No se puede activar DER, ya hay cambio a IZQUIERDA")
      self.params.put_bool("ForceLaneChangeLeft", False)
      self.params.put_bool("ForceLaneChangeRight", False)
      print(f"🛑 Ambos cancelados por conflicto DER-IZQ")
    else:
      self.params.put_bool("ForceLaneChangeRight", True)
      print(f"✅ Ejecutando cambio de carril DERECHA para {self.DongleID}")

  def handle_intervalos(self, payload):
    """Maneja el comando de intervalos."""
    if payload == "true":
      self.params.put_bool("intervalos_toggle", True)
      print("✅ intervalos_toggle activado")
    elif payload == "false":
      self.params.put_bool("intervalos_toggle", False)
      print("🛑 intervalos_toggle desactivado")
    else:
      print(f"⚠️ Valor no reconocido en intervalos: '{payload}'")

  def start(self):
    """Inicia el cliente MQTT de comandos."""
    print("🚀 Iniciando MQTT Comandos...")
    # El cliente ya se inicia automáticamente en el hilo

  def stop(self):
    """Detiene el cliente MQTT de comandos."""
    self.stop_event.set()
    self.mqttc.disconnect()
    print("🛑 MQTT Comandos detenido")

if __name__ == "__main__":
  comandos = MQTTComandos()
  comandos.start()

  try:
    while True:
      time.sleep(1)
  except KeyboardInterrupt:
    comandos.stop()

