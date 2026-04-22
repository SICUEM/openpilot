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
from .camera_sender import CameraSender

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
    self.init_camera_sender()
    self._link_camera_to_comandos()

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
    self.sm = messaging.SubMaster(self.lista_suscripciones)

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

  def init_camera_sender(self):
    """Inicializa el sistema de envío de imágenes de cámaras.
    La configuracion (enabled, frecuencia) se carga automaticamente
    desde /data/adripilot_camera_config.json si existe."""
    try:
      self.camera_sender = CameraSender(
        mqtt_client=self.mqttc,
        dongle_id=self.DongleID,
        camera_type="road",
        interval_seconds=2.0,  # Default, se sobreescribe si hay config persistida
      )
      self.camera_sender.start()
    except Exception:
      self.camera_sender = None

  def _link_camera_to_comandos(self):
    """Conecta el CameraSender con MQTTComandos para permitir control remoto desde la app."""
    if hasattr(self, 'camera_sender') and self.camera_sender is not None:
      self.comandos_mqtt.set_camera_sender(self.camera_sender)

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
        time.sleep(5)

  def on_connect(self, client, userdata, flags, rc):
    if rc == 0:
      self.conectado = True
      # "Cold start" sync: publicar nuestro estado actual como mensaje
      # RETAINED para que cualquier app que se conecte despues lo reciba
      # inmediatamente (sin necesidad de que el usuario mueva nada).
      #
      # Lo hacemos con un pequeno delay para dar tiempo a que el otro
      # cliente MQTT (mqtt_comandos, que tiene las suscripciones) procese
      # los retained que el broker le pueda estar entregando del lado app
      # (caso: el usuario cambio algo en la app mientras el Comma estaba
      # offline). Asi publicamos DESPUES de haber aplicado esos cambios
      # y nuestro retained refleja el estado real.
      threading.Timer(1.5, self._publish_state_snapshot_retained).start()
    else:
      self.conectado = False

  def _publish_state_snapshot_retained(self):
    """Publica el estado actual de SteerTorqueMode y config_jetson con retain=True.

    Se llama una vez al conectar MQTT. El broker guarda estos mensajes y los
    entrega instantaneamente a cualquier subscriber futuro (p.ej. la app al
    lanzarse). source='comma_ui' para que el anti-eco de mqtt_comandos.py
    ignore el retained cuando le llegue a el mismo por su suscripcion.
    """
    if not self.conectado:
      return
    try:
      # --- SteerTorqueMode ---
      mode_raw = self.params.get("SteerTorqueMode")
      try:
        mode = int(mode_raw) if mode_raw else 0
      except (ValueError, TypeError):
        mode = 0
      steer_payload = {
        "dongle_id": self.DongleID,
        "steer_torque_mode": mode,
        "source": "comma_ui",
        "timestamp": int(time.time() * 1000),
      }
      steer_str = json.dumps(steer_payload)
      self.mqttc.publish("steer_torque_mode/global", steer_str, qos=0, retain=True)
      self.mqttc.publish(f"telemetry_config/{self.DongleID}/steer_torque_mode", steer_str, qos=0, retain=True)
      print(f"[COLD-START SYNC] Retained SteerTorqueMode={mode} publicado")

      # --- config_jetson.json (IPs, puertos, calidad, enabled) ---
      config_path = os.path.join(self.base_path, "config_jetson.json")
      if os.path.exists(config_path):
        try:
          with open(config_path, "r") as f:
            cfg = json.load(f)
        except Exception:
          cfg = {}
        jetson_payload = {
          "dongle_id": self.DongleID,
          "jetson_enabled": cfg.get("jetson_enabled", False),
          "jetson_ip": cfg.get("jetson_ip", ""),
          "comma_ip": cfg.get("comma_ip", ""),
          "jetson_img_port": cfg.get("jetson_img_port", 5555),
          "jetson_torque_port": cfg.get("jetson_torque_port", 5556),
          "jpeg_quality": cfg.get("jpeg_quality", 80),
          "source": "comma_ui",
          "timestamp": int(time.time() * 1000),
        }
        jet_str = json.dumps(jetson_payload)
        self.mqttc.publish("jetson_config/global", jet_str, qos=0, retain=True)
        self.mqttc.publish(f"telemetry_config/{self.DongleID}/jetson_config", jet_str, qos=0, retain=True)
        print(f"[COLD-START SYNC] Retained jetson_config publicado: {jetson_payload}")
    except Exception as e:
      print(f"[COLD-START SYNC] ERROR publicando snapshot: {e}")

  def on_disconnect(self, client, userdata, rc):
    self.conectado = False

  def start(self):
    threading.Thread(target=self.loop, daemon=True).start()

  def stop(self):
    """Detiene el sistema MQTT completo."""
    self.stop_event.set()
    if hasattr(self, 'comandos_mqtt'):
      self.comandos_mqtt.stop()
    if hasattr(self, 'camera_sender') and self.camera_sender is not None:
      self.camera_sender.stop()
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

      # Publicar Jetson config si fue cambiada desde la UI del Comma
      try:
        jetson_payload = self.params.get("JetsonConfigMqttPayload")
        if jetson_payload and len(jetson_payload) > 2:
          payload_str = jetson_payload.decode('utf-8')
          print(f"[JETSON SYNC] Detectado JetsonConfigMqttPayload: {payload_str[:200]}")
          try:
            # retain=True: el broker guarda la ultima version de cada topic y
            # la entrega automaticamente a futuros subscribers. Asi la app al
            # lanzarse tiene el estado actual sin tener que preguntarle a nadie.
            result1 = self.mqttc.publish("jetson_config/global", payload_str, qos=0, retain=True)
            result2 = self.mqttc.publish(f"telemetry_config/{self.DongleID}/jetson_config", payload_str, qos=0, retain=True)
            print(f"[JETSON SYNC] Publicado (retained) a jetson_config/global rc={result1.rc}")
            print(f"[JETSON SYNC] Publicado (retained) a telemetry_config/{self.DongleID}/jetson_config rc={result2.rc}")
          except Exception as e:
            print(f"[JETSON SYNC] ERROR publicando MQTT: {e}")
          self.params.remove("JetsonConfigMqttPayload")
          print("[JETSON SYNC] Param JetsonConfigMqttPayload eliminado")
      except Exception as e:
        print(f"[JETSON SYNC] ERROR leyendo param: {e}")

      # Publicar SteerTorqueMode si fue cambiado desde la UI del Comma
      try:
        steer_mode_payload = self.params.get("SteerTorqueModeMqttPayload")
        if steer_mode_payload and len(steer_mode_payload) > 2:
          payload_str = steer_mode_payload.decode('utf-8')
          print(f"[STEER MODE SYNC] Detectado payload: {payload_str[:200]}")
          try:
            # retain=True: ver comentario arriba en JetsonConfig.
            result1 = self.mqttc.publish("steer_torque_mode/global", payload_str, qos=0, retain=True)
            result2 = self.mqttc.publish(f"telemetry_config/{self.DongleID}/steer_torque_mode", payload_str, qos=0, retain=True)
            print(f"[STEER MODE SYNC] Publicado (retained) a steer_torque_mode/global rc={result1.rc}")
            print(f"[STEER MODE SYNC] Publicado (retained) a telemetry_config/{self.DongleID}/steer_torque_mode rc={result2.rc}")
          except Exception as e:
            print(f"[STEER MODE SYNC] ERROR publicando MQTT: {e}")
          self.params.remove("SteerTorqueModeMqttPayload")
      except Exception as e:
        print(f"[STEER MODE SYNC] ERROR leyendo param: {e}")

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
              except Exception:
                self.conectado = False
            # Si no hay conexión, simplemente no enviar (no encolar)

      time.sleep(self.velocidadActualizacion)

  def enviar_datos_importantes(self, canal, datos):
    claves = self.keys_importantes_por_canal.get(canal, [])

    # Si no hay claves definidas, usar datos directamente sin copiar
    if not claves:
      datos["dongle_id"] = self.DongleID
      return datos
    else:
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
