#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
from datetime import datetime

import paho.mqtt.client as mqtt

def miLog(msg, code):
  fileLog = "/data/openpilot/sicuem/mqttDebug.txt"
  sttime = datetime.now().strftime('%Y/%m/%d_%H:%M:%S')
  f = open(fileLog, "a")
  f.write(f"[{sttime}] - {msg}. code:{code}\n")
  f.close()

def inventa(topic):
  sttime = datetime.now().strftime('%Y/%m/%d_%H:%M:%S')
  return (f"[{sttime}] texto de prueba en: "+topic)

class TopicMqtt:

  def __init__(self):
    fileJson = "/data/openpilot/sicuem/canales.json"
    self.espera = 0.5
    self.indice_canal = 0
    self.conetado = False
    self.ultimo = time.time()

    with open(fileJson, 'r') as f:
      jsondata = json.load(f)

    # Filtrar elementos con enable igual a 1
    self.enabled_items = [item for item in jsondata['canales'] if item['enable'] == 1]
    # Buscar Elemento Speed.
    speed_value = jsondata['config']['speed']['value']
    self.espera = 1.0 / float(speed_value)

    try:
      #broker_address = "195.235.211.197"
      broker_address = "mqtt.eclipseprojects.io"
      self.mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
      self.mqttc.on_connect = self.on_connect
      self.mqttc.on_disconnect = self.on_disconnect
      self.mqttc.on_subscribe = self.on_subscribe
      self.mqttc.connect(broker_address, 1883, 60)
      self.mqttc.subscribe("telemetry_config/speed", 0)
      self.mqttc.on_message = self.on_message
      self.mqttc.loop_start()
    except Exception as e:
      miLog("Error de conexion en TopicMqtt", e)

  def ping(self):
    miLog("Ping", "OK")

  def setCanalControlsd(self, sn):
    self.sm = sn

  def on_connect(self, mqttc, obj, flags, reason_code, properties):
    if reason_code == 0:
      self.conetado = True
      miLog("on_connect", reason_code)

  def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
    self.conetado = False
    miLog("on_disconnect", reason_code)


  def on_message(self, mqttc, obj, msg):
    self.espera = 1.0 / float(msg.payload.decode())
    miLog("on_message", f"{msg.topic}:{msg.payload.decode()}, value: {self.espera}")

  def on_subscribe(self, mqttc, obj, mid, reason_code_list, properties):
    miLog("on_subscribe", f"{mid}, {reason_code_list}")

  def loop(self):
    ahora = time.time()
    if ahora - self.ultimo > self.espera:  # Espera variable.
      canal_actual = self.enabled_items[self.indice_canal]
      #miLog("loop_in", canal_actual['topic'])
      self.mqttc.publish(canal_actual['topic'], str(self.sm[canal_actual['canal']]), qos=0)
      #self.mqttc.publish(canal_actual['topic'], inventa(canal_actual['canal']), qos=0)
      self.indice_canal = (self.indice_canal + 1) % len(self.enabled_items)
      self.ultimo = time.time()
