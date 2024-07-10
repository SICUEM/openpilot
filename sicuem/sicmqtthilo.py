#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
from datetime import datetime
from threading import Thread, Event             #-----------------------------------------------Adrian Cañadas Gallardo
from openpilot.common.params import Params
import cereal.messaging as messaging
import requests                                 #-----------------------------------------------Adrian Cañadas Gallardo
import paho.mqtt.client as mqtt

def miLog(msg, code):
  #fileLog = "/data/openpilot/sicuem/mqttDebug.txt"
  fileLog = "../../sicuem/mqttDebug.txt"
  sttime = datetime.now().strftime('%Y/%m/%d_%H:%M:%S')
  with open(fileLog, "a") as f:
    f.write(f"[{sttime}] - {msg}. code:{code}\n")

def inventa(topic):
  sttime = datetime.now().strftime('%Y/%m/%d_%H:%M:%S')
  return f"[{sttime}] texto de prueba en: {topic}"

class SicMqttHilo:

  def __init__(self):
    print("Iniciando SicMqttHilo")

  def inicializar(self):
    #fileJson = "/data/openpilot/sicuem/canales.json"
    fileJson = "../../sicuem/canales.json"
    self.espera = 0.5
    self.indice_canal = 0
    self.conetado = False
    self.pause_event = Event()    #-----------------------------------------------Adrian Cañadas Gallardo
    self.pause_event.set()        #-----------------------------------------------Adrian Cañadas Gallardo
    params = Params()
    self.DongleID = params.get("DongleId").decode('utf-8')
    if self.DongleID is None:
      self.DongleID = "DongleID"

    with open(fileJson, 'r') as f:
      jsondata = json.load(f)

     # -----------------------------------------------Adrian Cañadas Gallardo
    self.lista_suscripciones = [item['canal'] for item in jsondata['canales'] if item['enable'] == 1]
    self.enabled_items = [item for item in jsondata['canales'] if item['enable'] == 1]
    speed_value = jsondata['config']['speed']['value']
    self.espera = 1.0 / float(speed_value)
    send_value = int(jsondata['config']['send']['value'])
    miLog("Init send value:", send_value)
    if send_value == 0:
      self.pause_event.clear()
    self.broker_address = jsondata['config']['IpServer']['value']
    miLog("Default Server URL:", self.broker_address)

  def ping(self):
    miLog("Ping", "OK")



  def generar_lista_suscripciones(self):
    suscripciones = [item['topic'].format(self.DongleID) for item in self.jsondata['canales'] if item['enable'] == 1]
    return suscripciones
  def on_connect(self, mqttc, obj, flags, reason_code, properties):
    if reason_code == 0:
      self.conetado = True
      miLog("on_connect", reason_code)

  def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
    self.conetado = False
    miLog("on_disconnect", reason_code)

  def on_message(self, mqttc, obj, msg):
    if msg.topic == "telemetry_config/speed":
      self.espera = 1.0 / float(msg.payload.decode())
      miLog("on_message", f"{msg.topic}:{msg.payload.decode()}, value: {self.espera}")
  #-INI----------------------------------------------Adrian Cañadas Gallardo
    elif msg.topic == "telemetry_config/pausarHilo":
      value = int(msg.payload.decode())
      if value == 1:
        miLog("Hilo reanudado", "Set")
        self.pause_event.set()
      elif value == 0:
        miLog("Hilo pausado", "Clear")
        self.pause_event.clear()
  #---FIN--------------------------------------------Adrian Cañadas Gallardo

  def on_subscribe(self, mqttc, obj, mid, reason_code_list, properties):
    miLog("on_subscribe", f"{mid}, {reason_code_list}")

  #-INI----------------------------------------------Adrian Cañadas Gallardo
  def conexion(self, url='http://www.google.com', intervalo=5):
    conectado = False
    while not conectado:
      try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
          print("Conexión a Internet exitosa.")
          miLog("Conexión a Internet exitosa.", "OK")
          conectado = True
      except requests.ConnectionError:
        print(f"No hay conexión a Internet. Intentando nuevamente en {intervalo} segundos...")
        miLog("No hay conexión a Internet. Intentando nuevamente.", "ERROR")
        time.sleep(intervalo)
  #---FIN--------------------------------------------Adrian Cañadas Gallardo
    try:
      self.mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
      self.mqttc.on_connect = self.on_connect
      self.mqttc.on_disconnect = self.on_disconnect
      self.mqttc.on_subscribe = self.on_subscribe
      self.mqttc.on_message = self.on_message
      self.mqttc.connect(self.broker_address, 1883, 60)
      self.mqttc.subscribe("telemetry_config/speed", 0)
      self.mqttc.subscribe("telemetry_config/pausarHilo", 0)  #-----------------------------------------------Adrian Cañadas Gallardo 0 continuar, 1 pausar
      self.mqttc.loop_start()
      miLog("Conectado SicMqttHilo correctamente.", 0)
    except Exception as e:
      miLog("Error de conexión en TopicMqtt", e)

  def loop(self):
    self.conexion()
    while True:
      self.pause_event.wait()  #-----------------------------------------------Adrian Cañadas Gallardo
      self.sm.update()
      canal_actual = self.enabled_items[self.indice_canal]
      self.mqttc.publish(str(canal_actual['topic']).format(self.DongleID), str(self.sm[canal_actual['canal']]), qos=0)
      self.indice_canal = (self.indice_canal + 1) % len(self.enabled_items)
      time.sleep(self.espera)

  def leer_valor_sicmqtthilo(self):
    # Lee el archivo conf.json y extrae el valor de sicmqtthilo
    with open('conf.json', 'r') as archivo_conf:
      datos_conf = json.load(archivo_conf)
      sicmqtthilo = datos_conf.get('sicmqtthilo', 0)  # Valor predeterminado de 0 si no se encuentra

    return sicmqtthilo

  def start(self) -> int:

    #iniciar si en conf.json sicmqtthiloesta a 0 y cambiar a 1

    sicmqtthilo = leer_valor_sicmqtthilo()
    if sicmqtthilo == 0:
      self.inicializar()

      # actualiza el valor de sicmqtthilo en conf.json a 1
      with open('conf.json', 'w') as archivo_conf:
        datos_conf = {'sicmqtthilo': 1}
        json.dump(datos_conf, archivo_conf)





    self.sm = messaging.SubMaster(self.lista_suscripciones)   #-----------------------------------------------Adrian Cañadas Gallardo

    time.sleep(2)
    hilo = Thread(target=self.loop)
    hilo.start()
    miLog("Terminado programa principal", 0)
    return 0
