#!/usr/bin/env python3
import datetime
import time

import paho.mqtt.client as mqtt
import cereal.messaging as messaging

class ReadMessagefromSub:

  def __init__(self):
    self.ultimo = time.time()

    try:
      #broker_address = "192.168.1.184"
      broker_address="mqtt.eclipseprojects.io" #use external broker
      self.mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
      self.mqttc.connect(broker_address, 1883, 60)
    except Exception as e:
      f = open("demofile2.txt", "a")
      f.write("Now the file has more content!")
      f.write("Error en la conexion con el broker mqtt")
      f.write(e)
      f.close()
            
  def setCanalControlsd(self, sn):
    self.sm = sn

  def enviarAArchivo(self):
    self.añadir_contenido_txt_ssh( 'TELEMETRIA_OP', self.escribirEnTxtServ())

  def loop(self):
    ahora=time.time()
    if ahora-self.ultimo > 1:
      infot = self.mqttc.publish("sicuem/gps", str(self.sm['gpsLocationExternal']), qos=0)
      self.ultimo=time.time()

    self.mqttc.loop(0)
















