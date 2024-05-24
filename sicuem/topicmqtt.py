#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
from datetime import datetime
import subprocess
import sys
try:
  import paho.mqtt.client as mqtt
  paho_instaled = True
except ImportError:
  subprocess.Popen([sys.executable, "/data/openpilot/sicuem/installMqtt.py"])
  paho_instaled = False

class TopicMqtt:

  def __init__(self):
    self.fileDebug = "mqttDebug.txt"
    fileJson = "/data/openpilot/sicuem/canales.json"
    #fileJson = "canales.json"
    self.espera = 0.5
    self.indice_canal = 0
    self.conetado = False
    self.ultimo = time.time()
    self.pahoInstaled = paho_instaled

    if not self.pahoInstaled:
      return
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
      self.mqttc.on_subscribe = self.on_subscribe
      self.mqttc.connect(broker_address, 1883, 60)
      self.mqttc.subscribe("telemetry_config/speed", 0)
      self.mqttc.on_message = self.on_message
      self.mqttc.loop_start()
    except Exception as e:
      print("Error en la conexion con el broker mqtt")
      print(e)

  def ping(self):
    sttime = datetime.now().strftime('%Y/%m/%d_%H:%M:%S')
    f = open(self.fileDebug, "a")
    f.write(f"[{sttime}] ping...\n")
    f.close()

  def setCanalControlsd(self, sn):
    self.sm = sn

  def on_connect(self, mqttc, obj, flags, reason_code, properties):
    if reason_code == 0:
      self.conetado = True
      sttime = datetime.now().strftime('%Y/%m/%d_%H:%M:%S')
      f = open(self.fileDebug, "a")
      f.write(f"[{sttime}] on_connect: {reason_code}\n")
      f.close()

  def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
    self.conetado = False
    sttime = datetime.now().strftime('%Y/%m/%d_%H:%M:%S')
    f = open(self.fileDebug, "a")
    f.write(f"[{sttime}] on_disconnect: {reason_code}\n")
    f.close()

  def on_message(self, mqttc, obj, msg):
    self.espera = 1.0 / int(msg.payload.decode())
    sttime = datetime.now().strftime('%Y/%m/%d_%H:%M:%S')
    f = open(self.fileDebug, "a")
    f.write(f"[{sttime}] on_message -> {msg.topic}:{msg.payload.decode()}, value: {self.espera}\n")
    f.close()

  def on_subscribe(self, mqttc, obj, mid, reason_code_list, properties):
    sttime = datetime.now().strftime('%Y/%m/%d_%H:%M:%S')
    f = open(self.fileDebug, "a")
    f.write(f"[{sttime}] on_subscribe: {mid}, {reason_code_list}\n")
    f.close()

  def loop(self):
    if not self.pahoInstaled:
      return
    ahora = time.time()
    if ahora - self.ultimo > self.espera:  # Espera variable.
      canal_actual = self.enabled_items[self.indice_canal]
      self.mqttc.publish(canal_actual['topic'], str(self.sm[canal_actual['canal']]), qos=0)
      #self.mqttc.publish(canal_actual['topic'], inventa(canal_actual['canal']), qos=0)
      self.indice_canal = (self.indice_canal + 1) % len(self.enabled_items)
      self.ultimo = time.time()
    # self.mqttc.loop(0)
