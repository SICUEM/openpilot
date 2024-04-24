#!/usr/bin/env python3
import datetime
import time

import paho.mqtt.client as mqtt
import cereal.messaging as messaging

class TopicMqtt:

  def __init__(self):
    self.ultimo = time.time()
    try:
      #broker_address = "192.168.1.184"
      broker_address="mqtt.eclipseprojects.io"
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
    if ahora-self.ultimo > 1:
      infot = self.mqttc.publish("sicuem/gps", str(self.sm['driverMonitoringState']), qos=0)
      #infot = self.mqttc.publish("sicuem/gps", time.time(), qos=0)
      self.ultimo=time.time()

    self.mqttc.loop(0)
