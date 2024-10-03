#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
import signal
import sys
from datetime import datetime
from threading import Thread, Event
from openpilot.common.params import Params
import cereal.messaging as messaging
import requests
import paho.mqtt.client as mqtt



class SicMqttHilo:

  def __init__(self):
    # Inicialización de atributos y registro de la señal SIGINT (CTRL+C)
    signal.signal(signal.SIGINT, self.signal_handler)

    self.jsonCanales = "../../sicuem/canales.json"
    self.jsonConfig = "../../sicuem/config.json"
    self.espera = 0.5
    self.indice_canal = 0
    self.conetado = False
    self.sm = None  # Inicializar self.sm como None para verificar después si está disponible
    self.pause_event = Event()
    self.pause_event.set()
    params = Params()
    self.DongleID = params.get("DongleId").decode('utf-8') if params.get("DongleId") else "DongleID"
    self.cargar_canales()  # Cargar los canales habilitados al inicio

    with open(self.jsonConfig, 'r') as f:
      self.dataConfig = json.load(f)
    speed_value = self.dataConfig['config']['speed']['value']
    self.espera = 1.0 / float(speed_value)
    print("Init speed value:", speed_value)
    send_value = int(self.dataConfig['config']['send']['value'])
    print("Init send value:", send_value)
    if send_value == 0:
      self.pause_event.clear()
    self.broker_address = self.dataConfig['config']['IpServer']['value']
    print("Default Server URL:", self.broker_address)

  def signal_handler(self, sig, frame):
    """Manejador de la señal SIGINT para detener el programa de forma controlada."""
    print('Se recibió SIGINT (CTRL+C), cerrando el programa de manera controlada...')
    self.cleanup()
    sys.exit(0)

  def cleanup(self):
    """Función de limpieza para detener hilos o cerrar conexiones antes de salir."""
    self.pause_event.set()  # Detener los hilos si están esperando
    print("Limpieza completada, cerrando el programa.", "INFO")

  def verificar_toggle_canales(self, dataCanales):
    """Revisa los toggles asociados a los canales y actualiza su estado 'enable' en función de los valores en Params."""
    params = Params()

    for item in dataCanales['canales']:
      toggle_param_name = f"{item['canal']}_toggle"
      try:
        toggle_value = params.get_bool(toggle_param_name)
        if toggle_value is not None:
          nuevo_estado = 1 if toggle_value else 0
          if item['enable'] != nuevo_estado:
            print(f"Cambiando estado de {item['canal']} a {nuevo_estado} según {toggle_param_name}", "OK")
            self.cambiar_enable_canal(item['canal'], nuevo_estado)
      except Exception as e:
        print()
        #print(f"No se encontró un parámetro toggle para {item['canal']}. Manteniendo el estado actual.", "INFO")

  # Función para cargar los canales habilitados
  def cargar_canales(self):
    with open(self.jsonCanales, 'r') as f:
      dataCanales = json.load(f)

    # Llamar a la función que revisa los toggles de los canales
    self.verificar_toggle_canales(dataCanales)

    # Actualizar las listas de canales habilitados
    self.lista_suscripciones = [item['canal'] for item in dataCanales['canales']]
    self.enabled_items = [item for item in dataCanales['canales'] if item['enable'] == 1]

    # Si no hay ningún canal habilitado, usar un canal predeterminado
    if not self.lista_suscripciones:
      print("No hay canales habilitados. Suscribiéndose a un canal por defecto.", "INFO")
      self.lista_suscripciones = []
      self.enabled_items = []

    print("Canales cargados", len(self.enabled_items))

  # Función para cambiar el estado 'enable' de un canal
  def cambiar_enable_canal(self, canal, estado):
    with open(self.jsonCanales, 'r') as f:
      dataCanales = json.load(f)
    for item in dataCanales['canales']:
      if item['canal'] == canal:
        item['enable'] = estado
        print(f"Cambiando estado de {canal} a {estado}", "OK")
        break
    with open(self.jsonCanales, 'w') as f:
      json.dump(dataCanales, f, indent=4)
    self.cargar_canales()

  def pausar_envio(self):
    print("Hilo pausado", "Clear")
    print("NO ENVIANDO DATOS")
    self.pause_event.clear()
    self.dataConfig['config']['send']['value'] = 0

  def reanudar_envio(self):
    print("Hilo reanudado", "Set")
    print("ENVIANDO DATOS")
    self.pause_event.set()
    self.dataConfig['config']['send']['value'] = 1

  def on_connect(self, mqttc, obj, flags, reason_code, properties):
    if reason_code == 0:
      self.conetado = True
      print("on_connect", reason_code)

  def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
    self.conetado = False
    print("on_disconnect", reason_code)

  def on_message(self, mqttc, obj, msg):
    if msg.topic == "telemetry_config/speed":
      self.espera = 1.0 / float(msg.payload.decode())
      self.dataConfig['config']['speed']['value'] = float(msg.payload.decode())
      print("on_message", f"{msg.topic}:{msg.payload.decode()}, value: {self.espera}")
    elif msg.topic == "telemetry_config/pausarHilo":
      value = int(msg.payload.decode())
      self.dataConfig['config']['send']['value'] = value
      if value == 1:
        self.reanudar_envio()
      elif value == 0:
        self.pausar_envio()
    elif msg.topic == "telemetry_config/dataSender":
      print("on_message", f"telemetry_config/dataSender:, value: {msg.payload.decode()}")
      self.mqttc.publish("telemetry_config/dataSenderEcho", f"#{time.time()}#{msg.payload.decode()}#", qos=0)
    elif msg.topic == "telemetry_config/guardar":
      print("on_message", f"telemetry_config/guardar:, value: {msg.payload.decode()}")
      with open(self.jsonConfig, 'w') as f:
        json.dump(self.dataConfig, f, indent=4)
    elif msg.topic == "telemetry_config/pingEcho":
      ahora = time.time()
      envio = float(msg.payload.decode())
      tiempo = "{:.3f}".format(ahora - envio)
      self.mqttc.publish("telemetry_config/dataSenderEcho", f"{envio}->{ahora}=>{tiempo}", qos=0)

  def on_subscribe(self, mqttc, obj, mid, reason_code_list, properties):
    print("on_subscribe", f"{mid}, {reason_code_list}")

  def conexion(self, url='http://www.google.com', intervalo=5):
    conectado = False
    while not conectado:
      try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
          print("Conexión a Internet exitosa.")
          print("Conexión a Internet exitosa.", "OK")
          conectado = True
      except requests.ConnectionError:
        print(f"No hay conexión a Internet. Intentando nuevamente en {intervalo} segundos...")
        print("No hay conexión a Internet. Intentando nuevamente.", "ERROR")
        time.sleep(intervalo)
    try:
      self.mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
      self.mqttc.on_connect = self.on_connect
      self.mqttc.on_disconnect = self.on_disconnect
      self.mqttc.on_subscribe = self.on_subscribe
      self.mqttc.on_message = self.on_message
      self.mqttc.connect(self.broker_address, 1883, 60)
      self.mqttc.subscribe("telemetry_config/speed", 0)
      self.mqttc.subscribe("telemetry_config/pausarHilo", 0)
      self.mqttc.subscribe("telemetry_config/dataSender", 0)
      self.mqttc.subscribe("telemetry_config/guardar", 0)
      self.mqttc.subscribe("telemetry_config/pingEcho", 0)
      self.mqttc.loop_start()
      print("Conectado SicMqttHilo correctamente.", 0)
    except Exception as e:
      print("Error de conexión en TopicMqtt", e)

  def loop(self):
    self.conexion()
    hilo_ping = Thread(target=self.loopPing)
    hilo_ping.start()

    while True:
      self.pause_event.wait()
      self.cargar_canales()  # Recargar los canales habilitados en cada ciclo

      # Verificar si hay canales habilitados antes de continuar
      if len(self.enabled_items) > 0 and self.sm:  # Asegurarse de que self.sm esté inicializado
        for canal_actual in self.enabled_items:
          canal_nombre = canal_actual['canal']

          # Verificar si el canal está disponible en self.sm.data
          if canal_nombre in self.sm.data:
            try:
              self.sm.update()
              self.mqttc.publish(
                str(canal_actual['topic']).format(self.DongleID),
                str(self.sm[canal_nombre]),
                qos=0
              )
              print(f"Enviando datos para {canal_nombre}")
            except KeyError as e:
              print(f"Error al acceder a {canal_nombre}: {str(e)}", "ERROR")
              continue  # Continuar con el siguiente canal si ocurre un KeyError
          else:
            print(f"Canal {canal_nombre} no disponible en SubMaster.", "WARN")
      else:
        # Publicar por MQTT que no hay canales activados
        self.mqttc.publish("telemetry_mqtt/vacio", "ningun canal activado...", qos=0)

      print(f"telemetry_mqtt/#")
      time.sleep(self.espera)

  def loopPing(self):
    while True:
      self.pause_event.wait()
      self.mqttc.publish("telemetry_config/ping", str(time.time()), qos=0)
      print(f"telemetry_config/ping")
      time.sleep(3)

  def start(self) -> int:
    self.cargar_canales()  # Cargar los canales habilitados

    # Crear el objeto SubMaster aunque sea con el canal por defecto
    if self.lista_suscripciones:
      try:
        self.sm = messaging.SubMaster(['carState', 'controlsState', 'liveCalibration','carControl','gpsLocationExternal'])
      except Exception as e:
        print("Error creando SubMaster", str(e))
        self.sm = None  # Asegurarse de que self.sm esté definido

    time.sleep(2)

    hilo_telemetry = Thread(target=self.loop)
    hilo_telemetry.start()

    print("Terminado programa principal", 0)
    return 0
