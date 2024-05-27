#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
from datetime import datetime

import paho.mqtt.client as mqtt

def inventa(topic):
  sttime = datetime.now().strftime('%Y/%m/%d_%H:%M:%S')
  return (f"[{sttime}] texto de prueba en: "+topic)

class TopicMqtt:

  def __init__(self):
    self.fileDebug = "/data/openpilot/sicuem/mqttDebug.txt"
    fileJson = "/data/openpilot/sicuem/canales.json"
    #fileJson = "canales.json"
    self.espera = 0.5
    self.indice_canal = 0
    self.conetado = False
    self.ultimo = time.time()

    with open(fileJson, 'r') as f:
      jsondata = json.load(f)

    # Filtrar elementos con enable igual a 1
    self.enabled_items = [item for item in jsondata['canales'] if item['enable'] == 1]
    # Buscar Elemento Speed.
    speed_value = None
    for item in jsondata['config']:
      if 'speed' in item:
        speed_value = item['speed']
        break
    if speed_value is not None:
      self.espera = 1.0 / int(speed_value)


    try:
      broker_address = "195.235.211.197"
      #broker_address = "mqtt.eclipseprojects.io"
      self.mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
      self.mqttc.on_connect = self.on_connect
      self.mqttc.on_disconnect = self.on_disconnect
      #self.mqttc.on_subscribe = self.on_subscribe
      self.mqttc.connect(broker_address, 1883, 60)
      self.mqttc.subscribe("telemetry_config/speed", 0)
      self.mqttc.on_message = self.on_message
      self.mqttc.loop_start()
    except Exception as e:
      print("Error en la conexion con el broker mqtt")
      print(e)

  def setCanalControlsd(self, sn):
    self.sm = sn

  def on_connect(self, mqttc, obj, flags, reason_code, properties):
    if reason_code == 0:
      self.conetado = True

  def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
    self.conetado = False

  def on_message(self, mqttc, obj, msg):
    self.espera = 1.0 / float(msg.payload.decode())

  def loop(self):
    ahora = time.time()
    if ahora - self.ultimo > self.espera:  # Espera variable.
      canal_actual = self.enabled_items[self.indice_canal]
      self.mqttc.publish(canal_actual['topic'], str(self.sm[canal_actual['canal']]), qos=0)
      #self.mqttc.publish(canal_actual['topic'], inventa(canal_actual['canal']), qos=0)
      self.indice_canal = (self.indice_canal + 1) % len(self.enabled_items)
      self.ultimo = time.time()
