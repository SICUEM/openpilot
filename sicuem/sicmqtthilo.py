#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
from datetime import datetime
from threading import Thread
from openpilot.common.params import Params
import cereal.messaging as messaging
#-----------------------------------------------Adrian Cañadas Gallardo
import requests
#-----------------------------------------------Adrian Cañadas Gallardo

import paho.mqtt.client as mqtt

def miLog(msg, code):
  #fileLog = "/data/openpilot/sicuem/mqttDebug.txt"
  fileLog = "../../sicuem/mqttDebug.txt"
  sttime = datetime.now().strftime('%Y/%m/%d_%H:%M:%S')
  f = open(fileLog, "a")
  f.write(f"[{sttime}] - {msg}. code:{code}\n")
  f.close()

def inventa(topic):
  sttime = datetime.now().strftime('%Y/%m/%d_%H:%M:%S')
  return (f"[{sttime}] texto de prueba en: "+topic)

class SicMqttHilo:

  def __init__(self):
    #fileJson = "/data/openpilot/sicuem/canales.json"
    fileJson = "../../sicuem/canales.json"
    self.espera = 0.5
    self.indice_canal = 0
    self.conetado = False
    params = Params()
    self.DongleID = params.get("DongleId").decode('utf-8')
    if self.DongleID == None:
      self.DongleID = "DongleID"

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

  #-----------------------------------------------Adrian Cañadas Gallardo
  
  def verificar_conexion(self, url='http://www.google.com', intervalo=5):
    while True:
      try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
          print("Conexión a Internet exitosa.")
          miLog("Conexión a Internet exitosa.", "OK")
          return True
      except requests.ConnectionError:
        print("No hay conexión a Internet. Intentando nuevamente en {} segundos...".format(intervalo))
        miLog("No hay conexión a Internet. Intentando nuevamente.", "ERROR")
        time.sleep(intervalo)
  
  #-----------------------------------------------Adrian Cañadas Gallardo
  def loop(self):

    #-----------------------------------------------Adrian Cañadas Gallardo
    self.verificar_conexion()
    #-----------------------------------------------Adrian Cañadas Gallardo

    while True:
      canal_actual = self.enabled_items[self.indice_canal]
      self.mqttc.publish(str(canal_actual['topic']).format(self.DongleID), str(self.sm[canal_actual['canal']]), qos=0)
      #self.mqttc.publish(str(canal_actual['topic']).format(self.DongleID), inventa(canal_actual['canal']), qos=0)
      self.indice_canal = (self.indice_canal + 1) % len(self.enabled_items)
      time.sleep(self.espera)

  def start(self) -> int:
    self.sm = messaging.SubMaster(['accelerometer', 'androidLog', 'cameraOdometry', 'carControl', 'carOutput', 'carParams', 'carState',
                                   'controlsState', 'deviceState', 'driverCameraState', 'driverMonitoringState', 'driverStateV2',
                                   'gpsLocation', 'gpsLocationExternal', 'gyroscope', 'liveCalibration', 'liveLocationKalman', 'liveParameters',
                                   'liveTorqueParameters', 'logMessage', 'longitudinalPlan', 'longitudinalPlanSP', 'managerState', 'modelV2',
                                   'modelV2SP', 'pandaStates', 'peripheralState', 'radarState', 'roadCameraState', 'testJoystick',
                                   'wideRoadCameraState', 'mapRenderState'])
    time.sleep(2)
    hilo = Thread(target=self.loop)
    hilo.start()
    miLog("Terminado programa principal", 0)
    return 0
