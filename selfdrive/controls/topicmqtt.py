#!/usr/bin/env python3
import datetime
import time
import json

import paho.mqtt.client as mqtt
import cereal.messaging as messaging

class TopicMqtt:

  def __init__(self):
    self.ultimo = time.time()
    
    self.canales = []
    self.indice_canal = 1
    mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqttc.on_message = on_message
    mqttc.on_connect = on_connect
    mqttc.on_subscribe = on_subscribe
    # Uncomment to enable debug messages
    # mqttc.on_log = on_log
    mqttc.connect("mqtt.eclipseprojects.io", 1883, 60)
    mqttc.subscribe("$SYS/#")
    
    mqttc.loop_start()

    with open('../controls/canales.json', 'r') as f:
        data = json.load(f)

    for canal, valor in data.items():
        if valor == 1 and canal != "comentario":
            self.canales.append(canal)

    try:
      broker_address = "195.235.211.197"
      #broker_address="mqtt.eclipseprojects.io"
      self.mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
      self.mqttc.connect(broker_address, 1883, 60)
    except Exception as e:
      print("Error en la conexion con el broker mqtt")
      print(e)

  def ping(self):
    f = open("./mqtt.txt", "a")
    f.write("Ping....\n")
    f.close()

  def setCanalControlsd(self, sn):
    self.sm = sn

  def loop(self):
    ahora=time.time()
    if ahora-self.ultimo > 0.5:  # Cambiado a 500 milisegundos
      canal_actual = self.canales[self.indice_canal]
      self.mqttc.publish(canal_actual, str(self.sm[canal_actual.split('/')[-1]]), qos=0) # Publica el mensaje en el canal actual
      self.indice_canal = (self.indice_canal + 1) % len(self.canales) # Actualiza el índice del canal para la próxima publicación
      self.ultimo=time.time()
    self.mqttc.loop(0)

  def on_connect(self,mqttc, obj, flags, reason_code, properties):
      print("reason_code: " + str(reason_code))
  
  
  def on_message(self,mqttc, obj, msg):
      print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
  
  
  def on_subscribe(self,mqttc, obj, mid, reason_code_list, properties):
      print("Subscribed: " + str(mid) + " " + str(reason_code_list))
  
  
  def on_log(self,mqttc, obj, level, string):
      print(string)
    
  def on_disconnect(self,mqttc, obj, rc):
    print("Disconected reason_code: " + str(rc))

