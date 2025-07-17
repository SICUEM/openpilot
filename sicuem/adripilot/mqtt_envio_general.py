
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import time
import threading
import paho.mqtt.client as mqtt
import cereal.messaging as messaging
from openpilot.common.params import Params
import os

class MQTTEnvioGeneral:
  def __init__(self):
    self.modo_test = False  # Cambia a False si quieres datos reales

    self.velocidadActualizacion = 1
    self.base_path = os.path.dirname(os.path.abspath(__file__))  # ← ruta absoluta del script
    self.jsonConfig = os.path.join(self.base_path, "config_mqtt.json")
    self.jsonCanales = os.path.join(self.base_path, "canales.json")
    self.espera = 0.5
    self.pause_event = threading.Event()
    self.pause_event.set()
    self.stop_event = threading.Event()
    self.params = Params()
    self.DongleID = self.params.get("DongleId").decode("utf-8") if self.params.get("DongleId") else "DongleID"
    print(f"🆔 DongleID: {self.DongleID}")
    self.conectado = False
    self.load_config()
    self.cargar_canales()
    self.init_submaster()
    self.init_mqtt()

  def load_config(self):
    with open(self.jsonConfig, "r") as f:
      config = json.load(f)
      self.broker_address = config.get("broker", "localhost")

  def cargar_canales(self):
    with open(self.jsonCanales, "r") as f:
      data = json.load(f)
    self.enabled_items = [item for item in data["canales"] if item.get("enable") == 1]
    self.lista_suscripciones = [item["canal"] for item in self.enabled_items]
    self.keys_importantes_por_canal = {
      item["canal"]: item.get("keys_importantes", [])
      for item in self.enabled_items
    }

  def init_submaster(self):
    self.sm = messaging.SubMaster(self.lista_suscripciones)

  def init_mqtt(self):
    self.mqttc = mqtt.Client()
    self.mqttc.on_connect = self.on_connect
    self.mqttc.on_disconnect = self.on_disconnect
    self.mqttc.reconnect_delay_set(min_delay=1, max_delay=30)
    threading.Thread(target=self.setup_mqtt, daemon=True).start()

  def setup_mqtt(self):
    while not self.stop_event.is_set():
      try:
        self.mqttc.connect(self.broker_address, 1883, 60)
        if not self.conectado:
          self.mqttc.loop_start()
          self.conectado = True
          print("✅ Conectado al broker MQTT")
        break
      except Exception as e:
        print(f"❌ Error al conectar MQTT: {e}")
        time.sleep(5)

  def on_connect(self, client, userdata, flags, rc):
    print("🔌 MQTT conectado" if rc == 0 else f"🔌 Error conexión MQTT: {rc}")

  def on_disconnect(self, client, userdata, rc):
    self.conectado = False
    print("🔌 Desconectado MQTT. Reintentando...")

  def start(self):
    threading.Thread(target=self.loop, daemon=True).start()

  def loop(self):
    while not self.stop_event.is_set():
      self.pause_event.wait()
      self.sm.update()

      for canal in self.enabled_items:
        nombre = canal["canal"]
        topic = canal["topic"].format(self.DongleID)

        if self.modo_test:
          # Modo de prueba con datos fijos
          datos = {
            "dongle_id": self.DongleID,
            "nombre": "Hyundai Tucson",
            "vEgo": 14.2,
            "gas": 0.37
          }
          print(f"📤 [TEST] Enviando a {topic}: {datos}")
          self.mqttc.publish(topic, json.dumps(datos), qos=0)
          continue

        # Modo real
        if nombre in self.sm.data:
          if self.sm.updated[nombre]:
            datos = self.sm[nombre].to_dict()
            datos_filtrados = self.enviar_datos_importantes(nombre, datos)
            if datos_filtrados:
              print(f"📤 Enviando a {topic}: {datos_filtrados}")
              self.mqttc.publish(topic, json.dumps(datos_filtrados), qos=0)
            else:
              print(f"⚠️ No hay datos válidos para {nombre}, no se publica nada.")
          else:
            print(f"⏳ Canal {nombre} no actualizado todavía.")
        else:
          print(f"❌ Canal {nombre} no disponible en SubMaster.")

      time.sleep(self.velocidadActualizacion)

  def enviar_datos_importantes(self, canal, datos):
    claves = self.keys_importantes_por_canal.get(canal, [])
    resultado = {}

    for k in claves:
      if k in datos:
        resultado[k] = datos[k]
      else:
        print(f"⚠️ Clave {k} no está en los datos de {canal}")

    # Añadir siempre dongle_id y nombre
    resultado["dongle_id"] = self.DongleID
    resultado["nombre"] = "Hyundai Tucson"  # o puedes leerlo de Params o config si lo prefieres

    return resultado

  def enviar_datos_prueba(self):
    # Puedes reutilizar el topic y broker ya conectados
    topic = f"telemetry_mqtt/{self.DongleID}/carControl"
    datos = {
      "dongle_id": self.DongleID,
      "nombre": "Hyundai Tucson",
      "vEgo": 14.2,
      "gas": 0.37
    }
    print(f"📤 Enviando datos de prueba a {topic}: {datos}")
    self.mqttc.publish(topic, json.dumps(datos))


if __name__ == "__main__":
  sender = MQTTEnvioGeneral()
  sender.start()

  # Esperar conexión MQTT antes de publicar
  while not sender.conectado:
    print("⏳ Esperando conexión MQTT...")
    time.sleep(0.5)

  if sender.modo_test:
    sender.enviar_datos_prueba()

  while True:
    time.sleep(10)
