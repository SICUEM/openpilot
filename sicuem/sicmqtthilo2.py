#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import math
import time
import json
import signal
import sys
import os
from datetime import datetime
from threading import Thread, Event
from openpilot.common.params import Params
import cereal.messaging as messaging

import paho.mqtt.client as mqtt

class SicMqttHilo2:

  def __init__(self):
    # Inicialización de atributos y registro de la señal SIGINT (CTRL+C)
    signal.signal(signal.SIGINT, self.signal_handler)

    self.jsonCanales = "../../sicuem/canales.json"
    self.jsonConfig = "../../sicuem/config.json"
    self.espera = 0.5
    self.indice_canal = 0
    self.conectado = False
    self.sm = None
    self.pause_event = Event()
    self.pause_event.set()
    self.stop_event = Event()  # Evento para detener hilos de manera segura
    params = Params()
    self.params = params
    self.DongleID = params.get("DongleId").decode('utf-8') if params.get("DongleId") else "DongleID"
    self.cargar_canales()

    with open(self.jsonConfig, 'r') as f:
      self.dataConfig = json.load(f)
    speed_value = self.dataConfig['config']['speed']['value']
    self.espera = 1.0 / float(speed_value)
    send_value = int(self.dataConfig['config']['send']['value'])
    if send_value == 0:
      self.pause_event.clear()
    self.broker_address = self.dataConfig['config']['IpServer']['value']

    # Configurar el cliente MQTT
    '''self.mqttc = mqtt.Client()
    self.mqttc.on_connect = self.on_connect
    self.mqttc.on_disconnect = self.on_disconnect
    self.mqttc.on_message = self.on_message
    self.start_mqtt_thread()'''

  def start_mqtt_thread(self):
    """Inicia un hilo no bloqueante para manejar la conexión MQTT."""
    Thread(target=self.setup_mqtt_connection, daemon=True).start()

  def setup_mqtt_connection(self):
    while not self.stop_event.is_set():
      try:
        self.mqttc.connect(self.broker_address, 1883, 60)
        self.mqttc.subscribe("opmqttsender/messages", qos=0)
        self.mqttc.loop_start()
        self.conectado = True
        print("Conectado al broker MQTT con éxito.")
        break
      except Exception as e:
        print(f"Error al conectar con el broker MQTT: {e}")
        print("Reintentando conexión en 5 segundos...")
        time.sleep(5)

  def signal_handler(self, sig, frame):
    """Manejador de la señal SIGINT para detener el programa de forma controlada."""
    self.cleanup()
    sys.exit(0)

  def cleanup(self):
    """Cierra las conexiones y detiene los hilos de manera segura."""
    self.stop_event.set()  # Señal para detener los hilos
    if self.mqttc:
      self.mqttc.loop_stop()
      self.mqttc.disconnect()
    self.pause_event.set()

  def on_connect(self, client, userdata, flags, rc):
    if rc == 0:
      self.conectado = True
      print("Conectado al broker MQTT con éxito.")



  def on_disconnect(self, client, userdata, rc):
    """Maneja la desconexión del cliente MQTT y trata de reconectar."""
    self.conectado = False
    print("Desconectado del broker MQTT. Intentando reconectar...")
    self.start_mqtt_thread()

  def on_message(self, client, userdata, msg):
    """Maneja los mensajes recibidos en el tema MQTT."""
    if msg.topic == "opmqttsender/messages":
        message = msg.payload.decode()
        print(f"Mensaje recibido: {message}")
        self.params.put_bool_nonblocking("sender_uem_up", False)
        self.params.put_bool_nonblocking("sender_uem_down", False)
        self.params.put_bool_nonblocking("sender_uem_left", False)
        self.params.put_bool_nonblocking("sender_uem_right", False)
        if message == "up":
            self.params.put_bool_nonblocking("sender_uem_up", True)
        elif message == "down":
            self.params.put_bool_nonblocking("sender_uem_down", True)
        elif message == "left":
            self.params.put_bool_nonblocking("sender_uem_left", True)
        elif message == "right":
            self.params.put_bool_nonblocking("sender_uem_right", True)

  def verificar_toggle_canales(self, dataCanales):
    params = Params()
    for item in dataCanales['canales']:
      toggle_param_name = f"{item['canal']}_toggle"
      try:
        toggle_value = params.get_bool(toggle_param_name)
        if toggle_value is not None:
          nuevo_estado = 1 if toggle_value else 0
          if item['enable'] != nuevo_estado:
            self.cambiar_enable_canal(item['canal'], nuevo_estado)
      except Exception:
        pass

  def cargar_canales(self):
    """Carga la configuración de los canales desde un archivo JSON."""
    try:
      with open(self.jsonCanales, 'r') as f:
        dataCanales = json.load(f)
      self.verificar_toggle_canales(dataCanales)
      self.lista_suscripciones = [item['canal'] for item in dataCanales['canales']]
      self.enabled_items = [item for item in dataCanales['canales'] if item['enable'] == 1]
    except FileNotFoundError:
      print(f"Error: El archivo {self.jsonCanales} no existe.")
      self.lista_suscripciones = []
      self.enabled_items = []
    except json.JSONDecodeError as e:
      print(f"Error al cargar el archivo JSON {self.jsonCanales}: {e}")
      self.lista_suscripciones = []
      self.enabled_items = []

