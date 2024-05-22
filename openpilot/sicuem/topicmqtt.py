#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json

from datetime import datetime

paho_instaled = True
import subprocess
import sys
try:
  import paho.mqtt.client
except ImportError:
  print("Please install paho-mqtt");
  paho_instaled = False

class TopicMqtt:

  def __init__(self):
    self.fileDebug = "mqttDebug.txt"
    #fileJson = "canales.json"
    fileJson = "../controls/canales.json"
    self.indice_canal = 0
    self.conectado = False
    self.espera = 0.5
    self.ultimo = time.time()
    self.PahoInstaled = paho_instaled
    self.mqttc = 0

    with open(fileJson, 'r') as f:
      jsondata = json.load(f)

    # Filtrar elementos con enable igual a 1
    self.enabled_items = [item for item in jsondata['canales'] if item['enable'] == 1]
    # Buscar Elemento Speed.
    speed_value = jsondata['config']['speed']['value']
    self.espera = 1.0 / float(speed_value)

  def conectar(self):
    try:
      broker_address = "195.235.211.197"
      #broker_address = "mqtt.eclipseprojects.io"
      import paho.mqtt.client
      self.mqttc = paho.mqtt.client.Client(paho.mqtt.client.CallbackAPIVersion.VERSION2)
      self.mqttc.on_connect = self.on_connect
      self.mqttc.on_disconnect = self.on_disconnect
      self.mqttc.on_subscribe = self.on_subscribe
      self.mqttc.connect(broker_address, 1883, 60)
      self.mqttc.subscribe("telemetry_config/speed", 0)
      self.mqttc.on_message = self.on_message
      self.mqttc.loop_start()
      self.conectado = True
    except Exception as e:
      print("Error en la conexion con el broker mqtt")
      print(e)

  def ping(self):
    sttime = datetime.now().strftime('%Y/%m/%d_%H:%M:%S')
    f = open(self.fileDebug, "a")
    f.write(f"[{sttime}] ping...\n")
    f.close()

  def installPaho(self):
    ahora = time.time()
    if ahora - self.ultimo > 5:  # Espera 3 sec.
      self.PahoInstaled = True
      try:
        import paho.mqtt.client
        print("import paho.mqtt.client")
      except ImportError:
        print("Error install paho-mqtt");
        code = subprocess.call([sys.executable, "-m", "pip", "install", "paho-mqtt"])
        self.PahoInstaled = False
        print("** Code:", code, ", PahoInstaled:", self.PahoInstaled)
      self.ultimo = time.time()

  def setCanalControlsd(self, sn):
    self.sm = sn

  def on_connect(self, mqttc, obj, flags, reason_code, properties):
    if reason_code == 0:
      self.conectado = True
      sttime = datetime.now().strftime('%Y/%m/%d_%H:%M:%S')
      f = open(self.fileDebug, "a")
      f.write(f"[{sttime}] on_connect: {reason_code}\n")
      f.close()

  def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
    self.conectado = False
    sttime = datetime.now().strftime('%Y/%m/%d_%H:%M:%S')
    f = open(self.fileDebug, "a")
    f.write(f"[{sttime}] on_disconnect: {reason_code}\n")
    f.close()

  def on_message(self, mqttc, obj, msg):
    self.espera = 1.0 / float(msg.payload.decode())
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
    if not self.PahoInstaled:
      self.installPaho()
      return
    if not self.conectado:
      self.conectar()
      return
    ahora = time.time()
    if ahora - self.ultimo > self.espera:  # Espera variable.
      canal_actual = self.enabled_items[self.indice_canal]
      self.mqttc.publish(canal_actual['topic'], str(self.sm[canal_actual['canal']]), qos=0)
      self.indice_canal = (self.indice_canal + 1) % len(self.enabled_items)
      self.ultimo = time.time()
    # self.mqttc.loop(0)
