#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import time
import threading
import paho.mqtt.client as mqtt
import cereal.messaging as messaging
from openpilot.common.params import Params
import os
from .mqtt_comandos import MQTTComandos

class MQTTEnvioGeneral:
  def __init__(self):
    self.velocidadActualizacion = 1
    self.base_path = os.path.dirname(os.path.abspath(__file__))
    self.jsonConfig = os.path.join(self.base_path, "config_mqtt.json")
    self.jsonCanales = os.path.join(self.base_path, "canales.json")
    self.espera = 0.5
    self.pause_event = threading.Event()
    self.pause_event.set()
    self.stop_event = threading.Event()
    self.params = Params()
    self.DongleID = self.params.get("DongleId").decode("utf-8") if self.params.get("DongleId") else "DongleID"
    self.conectado = False
    self.load_config()
    self.cargar_canales()
    self.init_submaster()
    self.init_mqtt()
    self.init_comandos()

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
    # Agregar canales adicionales que se usan en sicmqtthilo2.py
    canales_adicionales = ['controlsState', 'liveCalibration', 'gpsLocation']
    lista_completa = self.lista_suscripciones + canales_adicionales
    self.sm = messaging.SubMaster(lista_completa)

  def init_mqtt(self):
    self.mqttc = mqtt.Client()
    self.mqttc.on_connect = self.on_connect
    self.mqttc.on_disconnect = self.on_disconnect
    self.mqttc.reconnect_delay_set(min_delay=1, max_delay=30)
    threading.Thread(target=self.setup_mqtt, daemon=True).start()

  def init_comandos(self):
    """Inicializa el sistema de comandos MQTT."""
    self.comandos_mqtt = MQTTComandos()
    self.comandos_mqtt.start()

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

  def stop(self):
    """Detiene el sistema MQTT completo."""
    self.stop_event.set()
    if hasattr(self, 'comandos_mqtt'):
      self.comandos_mqtt.stop()
    self.mqttc.disconnect()
    print("🛑 Sistema MQTT detenido")

  def loop(self):
    while not self.stop_event.is_set():
      self.pause_event.wait()
      self.sm.update()

      for canal in self.enabled_items:
        nombre = canal["canal"]
        topic = canal["topic"].format(self.DongleID)

        if nombre in self.sm.data and self.sm.updated[nombre]:
          datos = self.sm[nombre].to_dict()
          datos_filtrados = self.enviar_datos_importantes(nombre, datos)
          if datos_filtrados:
            print(f"📤 Enviando a {topic}: {datos_filtrados}")
            self.mqttc.publish(topic, json.dumps(datos_filtrados), qos=0)

      # Enviar datos adicionales de canales que no están en enabled_items pero están disponibles
      canales_adicionales = ['controlsState', 'liveCalibration', 'gpsLocation']
      for canal_nombre in canales_adicionales:
        if canal_nombre in self.sm.data and self.sm.updated[canal_nombre]:
          datos = self.sm[canal_nombre].to_dict()
          # Crear topic para canal adicional
          topic_adicional = f"telemetry_mqtt/{self.DongleID}/{canal_nombre}"
          datos_filtrados = self.enviar_datos_importantes(canal_nombre, datos)
          if datos_filtrados:
            print(f"📤 Enviando canal adicional a {topic_adicional}: {datos_filtrados}")
            self.mqttc.publish(topic_adicional, json.dumps(datos_filtrados), qos=0)

      time.sleep(self.velocidadActualizacion)

  def enviar_datos_importantes(self, canal, datos):
    claves = self.keys_importantes_por_canal.get(canal, [])

    # Si no hay claves definidas o está vacío, enviar TODOS los datos
    if not claves:
      resultado = datos.copy()
    else:
      # Si hay claves definidas, usar solo esas (aunque ahora están vacías)
      resultado = {k: datos[k] for k in claves if k in datos}

    resultado["dongle_id"] = self.DongleID
    return resultado

if __name__ == "__main__":
  sender = MQTTEnvioGeneral()
  sender.start()

  while not sender.conectado:
    time.sleep(0.5)

  while True:
    time.sleep(10)
