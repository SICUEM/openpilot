#!/usr/bin/env python3
import datetime
import time

import paho.mqtt.client as mqtt
import cereal.messaging as messaging

class TopicMqtt:

  def __init__(self):
    self.ultimo = time.time()
    self.canales = ["telemetry_mqtt/driverMonitoringState", "telemetry_mqtt/deviceState", "telemetry_mqtt/liveCalibration", 
                     "telemetry_mqtt/longitudinalPlan", "telemetry_mqtt/liveLocationKalman", 
                     "telemetry_mqtt/liveParameters", "telemetry_mqtt/liveTorqueParameters", 
                     "telemetry_mqtt/longitudinalPlanSP"]
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
