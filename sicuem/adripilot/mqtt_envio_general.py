#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import time
import threading
import paho.mqtt.client as mqtt
import cereal.messaging as messaging
from openpilot.common.params import Params
import os
from .mqtt_comandos import MQTTComandos
# from .camera_sender import CameraSender  # DESACTIVADO temporalmente - dando problemas

class MQTTEnvioGeneral:
  def __init__(self):
    self.velocidadActualizacion = 1
    self.base_path = os.path.dirname(os.path.abspath(__file__))
    self.jsonConfig = os.path.join(self.base_path, "config_mqtt.json")
    self.jsonCanales = os.path.join(self.base_path, "canales.json")
    self.espera = 0.5
    self.pause_event = threading.Event()
    self.pause_event.set()
    self.stop_event = threading.Event()
    self.params = Params()
    self.DongleID = self.params.get("DongleId").decode("utf-8") if self.params.get("DongleId") else "DongleID"
    self.conectado = False
    self.load_config()
    self.cargar_canales()
    self.init_submaster()
    self.init_mqtt()
    self.init_comandos()
    # self.init_camera_sender()  # DESACTIVADO temporalmente - dando problemas

  def load_config(self):
    with open(self.jsonConfig, "r") as f:
      config = json.load(f)
      self.broker_address = config.get("broker", "localhost")
      self.broker_port = int(config.get("broker_port", 1883))

  def cargar_canales(self):
    with open(self.jsonCanales, "r") as f:
      data = json.load(f)
    self.enabled_items = [item for item in data["canales"] if item.get("enable") == 1]
    self.lista_suscripciones = [item["canal"] for item in self.enabled_items]
    self.keys_importantes_por_canal = {
      item["canal"]: item.get("keys_importantes", [])
      for item in self.enabled_items
    }

  def init_submaster(self):
    # Agregar canales adicionales que se usan en sicmqtthilo2.py
    canales_adicionales = ['controlsState', 'liveCalibration', 'gpsLocation']
    lista_completa = self.lista_suscripciones + canales_adicionales
    self.sm = messaging.SubMaster(lista_completa)

  def init_mqtt(self):
    self.mqttc = mqtt.Client()
    self.mqttc.max_queued_messages_set(0)  # No encolar mensajes en RAM si no hay conexión
    self.mqttc.on_connect = self.on_connect
    self.mqttc.on_disconnect = self.on_disconnect
    self.mqttc.reconnect_delay_set(min_delay=1, max_delay=30)
    threading.Thread(target=self.setup_mqtt, daemon=True).start()

  def init_comandos(self):
    """Inicializa el sistema de comandos MQTT."""
    self.comandos_mqtt = MQTTComandos()
    self.comandos_mqtt.start()

  # DESACTIVADO temporalmente - dando problemas
  # def init_camera_sender(self):
  #   """Inicializa el sistema de envío de imágenes de cámaras."""
  #   try:
  #     # Configuración: calidad baja, frame rate alto (cada 2 segundos)
  #     # Resolución: 320x180 (pequeña pero suficiente para visualización)
  #     # Calidad JPEG: 35% (baja para reducir tamaño)
  #     self.camera_sender = CameraSender(
  #       camera_type="road",  # Solo road camera inicialmente
  #       interval_seconds=2.0,  # Cada 2 segundos (0.5 FPS)
  #       thumbnail_size=(320, 180),  # Resolución pequeña
  #       quality=35  # Calidad baja
  #     )
  #     self.camera_sender.start()
  #     print("📷 CameraSender iniciado para road camera")
  #   except Exception as e:
  #     print(f"⚠️ Error iniciando CameraSender: {e}")
  #     self.camera_sender = None

  def setup_mqtt(self):
    while not self.stop_event.is_set():
      try:
        self.mqttc.connect(self.broker_address, self.broker_port, 60)
        if not self.conectado:
          self.mqttc.loop_start()
          # Esperar un momento para que se establezca la conexión
          time.sleep(0.5)
        break
      except Exception:
        pass  # Error silenciado para reducir uso de memoria
        time.sleep(5)

  def on_connect(self, client, userdata, flags, rc):
    if rc == 0:
      self.conectado = True
    else:
      self.conectado = False

  def on_disconnect(self, client, userdata, rc):
    self.conectado = False

  def start(self):
    threading.Thread(target=self.loop, daemon=True).start()

  def stop(self):
    """Detiene el sistema MQTT completo."""
    self.stop_event.set()
    if hasattr(self, 'comandos_mqtt'):
      self.comandos_mqtt.stop()
    # DESACTIVADO temporalmente - dando problemas
    # if hasattr(self, 'camera_sender') and self.camera_sender is not None:
    #   self.camera_sender.stop()
    self.mqttc.disconnect()
    # print("🛑 Sistema MQTT detenido")  # Comentado para reducir uso de memoria

  def loop(self):
    while not self.stop_event.is_set():
      self.pause_event.wait()
      self.sm.update()

      # Verificar conexión antes de intentar enviar (evita encolar mensajes)
      # Usar verificación más simple: si está conectado según el callback
      is_connected = self.conectado
      # También verificar el estado real del cliente si está disponible
      if hasattr(self.mqttc, 'is_connected'):
        is_connected = is_connected and self.mqttc.is_connected()

      if not is_connected:
        # Sin conexión: no procesar ni encolar mensajes para evitar saturación de RAM
        # Log ocasional para debug (cada 50 iteraciones = ~50 segundos)
        if hasattr(self, '_no_connection_log_counter'):
          self._no_connection_log_counter += 1
        else:
          self._no_connection_log_counter = 0

        # Log eliminado para reducir uso de memoria

        time.sleep(self.velocidadActualizacion)
        continue

      # Resetear contador si hay conexión
      if hasattr(self, '_no_connection_log_counter'):
        self._no_connection_log_counter = 0

      for canal in self.enabled_items:
        nombre = canal["canal"]
        topic = canal["topic"].format(self.DongleID)

        if nombre in self.sm.data and self.sm.updated[nombre]:
          datos = self.sm[nombre].to_dict()
          datos_filtrados = self.enviar_datos_importantes(nombre, datos)
          if datos_filtrados:
            # Verificar conexión nuevamente antes de cada publicación
            if self.conectado:
              # Verificar también el estado real si está disponible
              if hasattr(self.mqttc, 'is_connected') and not self.mqttc.is_connected():
                continue
              try:
                self.mqttc.publish(topic, json.dumps(datos_filtrados), qos=0)
              except Exception as e:
                pass  # Error silenciado para reducir uso de memoria
                self.conectado = False
            # Si no hay conexión, simplemente no enviar (no encolar)

      # Enviar datos adicionales de canales que no están en enabled_items pero están disponibles
      canales_adicionales = ['controlsState', 'liveCalibration', 'gpsLocation']
      for canal_nombre in canales_adicionales:
        if canal_nombre in self.sm.data and self.sm.updated[canal_nombre]:
          datos = self.sm[canal_nombre].to_dict()
          # Crear topic para canal adicional
          topic_adicional = f"telemetry_mqtt/{self.DongleID}/{canal_nombre}"
          datos_filtrados = self.enviar_datos_importantes(canal_nombre, datos)
          if datos_filtrados:
            # Verificar conexión nuevamente antes de cada publicación
            if self.conectado:
              # Verificar también el estado real si está disponible
              if hasattr(self.mqttc, 'is_connected') and not self.mqttc.is_connected():
                continue
              try:
                self.mqttc.publish(topic_adicional, json.dumps(datos_filtrados), qos=0)
              except Exception as e:
                pass  # Error silenciado para reducir uso de memoria
                self.conectado = False
            # Si no hay conexión, simplemente no enviar (no encolar)

      time.sleep(self.velocidadActualizacion)

  def enviar_datos_importantes(self, canal, datos):
    claves = self.keys_importantes_por_canal.get(canal, [])

    # Si no hay claves definidas o está vacío, enviar TODOS los datos
    if not claves:
      resultado = datos.copy()
    else:
      # Si hay claves definidas, usar solo esas (aunque ahora están vacías)
      resultado = {k: datos[k] for k in claves if k in datos}

    resultado["dongle_id"] = self.DongleID
    return resultado

if __name__ == "__main__":
  sender = MQTTEnvioGeneral()
  sender.start()

  while not sender.conectado:
    time.sleep(0.5)

  while True:
    time.sleep(10)
