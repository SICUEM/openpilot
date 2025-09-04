#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import time
import threading
import paho.mqtt.client as mqtt
import cereal.messaging as messaging
from openpilot.common.params import Params
import os

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

  def load_config(self):
    with open(self.jsonConfig, "r") as f:
      config = json.load(f)
      self.broker_address = config.get("broker", "localhost")

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
    # Usar todos los canales disponibles para máxima telemetría
    canales_completos = [
      'carState', 'controlsState', 'liveCalibration', 'carControl',
      'gpsLocationExternal', 'gpsLocation', 'navInstruction',
      'radarState', 'drivingModelData'
    ]
    self.sm = messaging.SubMaster(canales_completos)

  def init_mqtt(self):
    self.mqttc = mqtt.Client()
    self.mqttc.on_connect = self.on_connect
    self.mqttc.on_disconnect = self.on_disconnect
    self.mqttc.on_message = self.on_message
    self.mqttc.reconnect_delay_set(min_delay=1, max_delay=30)
    threading.Thread(target=self.setup_mqtt, daemon=True).start()

  def setup_mqtt(self):
    while not self.stop_event.is_set():
      try:
        self.mqttc.connect(self.broker_address, 1883, 60)
        if not self.conectado:
          self.mqttc.loop_start()
          self.conectado = True
          print("✅ Conectado al broker MQTT")
          # Suscribirse a los topics de comandos
          self.mqttc.subscribe("telemetry_config/+/intervalos", qos=0)
          self.mqttc.subscribe("telemetry_config/+/left", qos=0)
          self.mqttc.subscribe("telemetry_config/+/right", qos=0)
          print("📡 Suscrito a topics de comandos de intervalos y cambio de carril")
        break
      except Exception as e:
        print(f"❌ Error al conectar MQTT: {e}")
        time.sleep(5)

  def on_connect(self, client, userdata, flags, rc):
    if rc == 0:
      print("🔌 MQTT conectado")
      # Enviar estado inicial de los parámetros
      self.enviar_estado_inicial()
    else:
      print(f"🔌 Error conexión MQTT: {rc}")

  def enviar_estado_inicial(self):
    """Envía el estado inicial de los parámetros de control."""
    try:
      # Estado de intervalos
      intervalos_actual = self.params.get_bool("intervalos_toggle")
      estado_intervalos = "on" if intervalos_actual else "off"
      self.mqttc.publish(f"telemetry_mqtt/{self.DongleID}/intervalos_status", estado_intervalos, qos=0)
      print(f"📡 Estado inicial intervalos enviado: {estado_intervalos}")

      # Estado de cambio de carril
      left_actual = self.params.get_bool("ForceLaneChangeLeft")
      right_actual = self.params.get_bool("ForceLaneChangeRight")

      if left_actual:
        self.mqttc.publish(f"telemetry_mqtt/{self.DongleID}/lane_change_status", "left", qos=0)
        print("📡 Estado inicial cambio de carril: IZQUIERDA")
      elif right_actual:
        self.mqttc.publish(f"telemetry_mqtt/{self.DongleID}/lane_change_status", "right", qos=0)
        print("📡 Estado inicial cambio de carril: DERECHA")
      else:
        self.mqttc.publish(f"telemetry_mqtt/{self.DongleID}/lane_change_status", "none", qos=0)
        print("📡 Estado inicial cambio de carril: NINGUNO")

    except Exception as e:
      print(f"❌ Error al enviar estado inicial: {e}")

  def on_disconnect(self, client, userdata, rc):
    self.conectado = False
    print("🔌 Desconectado MQTT. Reintentando...")
    # Re-suscribirse a los topics cuando se reconecte
    threading.Thread(target=self.reconnect_with_subscriptions, daemon=True).start()

  def reconnect_with_subscriptions(self):
    """Reconecta y re-suscribe a los topics de comandos."""
    while not self.stop_event.is_set() and not self.conectado:
      try:
        time.sleep(2)
        if self.mqttc.is_connected():
          self.mqttc.subscribe("telemetry_config/+/intervalos", qos=0)
          self.mqttc.subscribe("telemetry_config/+/left", qos=0)
          self.mqttc.subscribe("telemetry_config/+/right", qos=0)
          print("📡 Re-suscrito a topics de comandos tras reconexión")
          break
      except Exception as e:
        print(f"❌ Error al re-suscribirse: {e}")
        time.sleep(5)

  def on_message(self, client, userdata, msg):
    """Callback que maneja los mensajes MQTT de comandos."""
    try:
      # Comando de intervalos
      if msg.topic.startswith("telemetry_config/") and msg.topic.endswith("/intervalos"):
        partes = msg.topic.split("/")
        if len(partes) >= 3:
          id_coma = partes[1]
          if id_coma == self.DongleID:
            payload = msg.payload.decode(errors="ignore").strip().lower()
            print(f"🎯 Comando de intervalos recibido para ID: {id_coma}")
            if payload == "true":
              self.params.put_bool("intervalos_toggle", True)
              self.mqttc.publish(f"telemetry_mqtt/{self.DongleID}/intervalos_status", "on", qos=0)
              print("✅ intervalos_toggle activado")
            elif payload == "false":
              self.params.put_bool("intervalos_toggle", False)
              self.mqttc.publish(f"telemetry_mqtt/{self.DongleID}/intervalos_status", "off", qos=0)
              print("🛑 intervalos_toggle desactivado")
            else:
              print(f"⚠️ Valor no reconocido en intervalos: '{payload}'")
          else:
            print(f"🚫 ID no coincide para intervalos (esperado: {self.DongleID}, recibido: {id_coma})")

      # Comando de cambio de carril a la izquierda
      elif msg.topic.startswith("telemetry_config/") and msg.topic.endswith("/left"):
        partes = msg.topic.split("/")
        if len(partes) >= 3 and partes[1] == self.DongleID:
          payload = msg.payload.decode(errors="ignore").strip().lower()

          # Verificar toggle de seguridad c_carril
          if not self.params.get_bool("c_carril"):
            print("🛑 Cambio de carril a IZQUIERDA bloqueado por toggle c_carril.")
            return

          if payload == "false":
            self.params.put_bool("ForceLaneChangeLeft", False)
            self.params.put_bool("ForceLaneChangeRight", False)
            self.mqttc.publish(f"telemetry_mqtt/{self.DongleID}/lane_change_status", "none", qos=0)
            print("🛑 Cambio de carril cancelado (left=false)")
          elif self.params.get_bool("ForceLaneChangeRight"):
            print("⚠️ No se puede activar IZQ, ya hay cambio a DERECHA")
            self.params.put_bool("ForceLaneChangeLeft", False)
            self.params.put_bool("ForceLaneChangeRight", False)
            self.mqttc.publish(f"telemetry_mqtt/{self.DongleID}/lane_change_status", "none", qos=0)
            print("🛑 Ambos cancelados por conflicto IZQ-DER")
          else:
            self.params.put_bool("ForceLaneChangeLeft", True)
            self.mqttc.publish(f"telemetry_mqtt/{self.DongleID}/lane_change_status", "left", qos=0)
            print("✅ IZQUIERDA activado")

      # Comando de cambio de carril a la derecha
      elif msg.topic.startswith("telemetry_config/") and msg.topic.endswith("/right"):
        partes = msg.topic.split("/")
        if len(partes) >= 3 and partes[1] == self.DongleID:
          payload = msg.payload.decode(errors="ignore").strip().lower()

          # Verificar toggle de seguridad c_carril
          if not self.params.get_bool("c_carril"):
            print("🛑 Cambio de carril a DERECHA bloqueado por toggle c_carril.")
            return

          if payload == "false":
            self.params.put_bool("ForceLaneChangeLeft", False)
            self.params.put_bool("ForceLaneChangeRight", False)
            self.mqttc.publish(f"telemetry_mqtt/{self.DongleID}/lane_change_status", "none", qos=0)
            print("🛑 Cambio de carril cancelado (right=false)")
          elif self.params.get_bool("ForceLaneChangeLeft"):
            self.params.put_bool("ForceLaneChangeLeft", False)
            self.params.put_bool("ForceLaneChangeRight", False)
            self.mqttc.publish(f"telemetry_mqtt/{self.DongleID}/lane_change_status", "none", qos=0)
            print("⚠️ Ignorado right: había cambio a IZQUIERDA activo → ambos cancelados")
          else:
            self.params.put_bool("ForceLaneChangeRight", True)
            self.mqttc.publish(f"telemetry_mqtt/{self.DongleID}/lane_change_status", "right", qos=0)
            print("✅ Cambio de carril forzado a la DERECHA")

    except Exception as e:
      print(f"❌ Error al procesar mensaje MQTT: {e}")

  def start(self):
    threading.Thread(target=self.loop, daemon=True).start()

  def loop(self):
    while not self.stop_event.is_set():
      self.pause_event.wait()
      self.sm.update()

      for canal in self.enabled_items:
        nombre = canal["canal"]
        topic = canal["topic"].format(self.DongleID)

        if nombre in self.sm.data and self.sm.updated[nombre]:
          datos = self.sm[nombre].to_dict()
          datos_filtrados = self.enviar_datos_importantes(nombre, datos)
          if datos_filtrados:
            print(f"📤 Enviando a {topic}: {datos_filtrados}")
            self.mqttc.publish(topic, json.dumps(datos_filtrados), qos=0)

      # Enviar resumen de telemetría principal cada 5 segundos
      if int(time.time()) % 5 == 0:
        self.enviar_resumen_telemetria()

      time.sleep(self.velocidadActualizacion)

  def enviar_datos_importantes(self, canal, datos):
    claves = self.keys_importantes_por_canal.get(canal, [])
    resultado = {k: datos[k] for k in claves if k in datos}
    resultado["dongle_id"] = self.DongleID

    # Agregar timestamp para sincronización
    resultado["timestamp"] = time.time()

    # Agregar datos calculados importantes
    if canal == "carState":
      # Calcular velocidad en km/h
      if "vEgo" in resultado:
        resultado["vEgo_kmh"] = resultado["vEgo"] * 3.6

      # Calcular aceleración en m/s²
      if "aEgo" in resultado:
        resultado["aEgo_ms2"] = resultado["aEgo"]

    elif canal == "carControl":
      # Extraer setSpeed del hudControl
      if "hudControl" in resultado and isinstance(resultado["hudControl"], dict):
        hud = resultado["hudControl"]
        if "setSpeed" in hud:
          resultado["setSpeed_ms"] = hud["setSpeed"]
          resultado["setSpeed_kmh"] = hud["setSpeed"] * 3.6

    elif canal in ["gpsLocationExternal", "gpsLocation"]:
      # Agregar información de precisión GPS
      if "latitude" in resultado and "longitude" in resultado:
        resultado["gps_valid"] = True
        resultado["gps_coords"] = f"{resultado['latitude']:.6f},{resultado['longitude']:.6f}"
      else:
        resultado["gps_valid"] = False

    return resultado

  def enviar_resumen_telemetria(self):
    """Envía un resumen de telemetría principal con los datos más importantes."""
    try:
      if not self.sm:
        return

      self.sm.update()

      # Recopilar datos principales
      resumen = {
        "dongle_id": self.DongleID,
        "timestamp": time.time(),
        "velocidad": {},
        "aceleracion": {},
        "gps": {},
        "control": {},
        "radar": {}
      }

      # Datos de velocidad y aceleración
      if "carState" in self.sm.data and self.sm.updated["carState"]:
        car_state = self.sm["carState"].to_dict()
        resumen["velocidad"] = {
          "vEgo": car_state.get("vEgo", 0),
          "vEgo_kmh": car_state.get("vEgo", 0) * 3.6,
          "vCruise": car_state.get("vCruise", 0),
          "vCruise_kmh": car_state.get("vCruise", 0) * 3.6,
          "standstill": car_state.get("standstill", False)
        }
        resumen["aceleracion"] = {
          "aEgo": car_state.get("aEgo", 0),
          "aEgo_ms2": car_state.get("aEgo", 0),
          "gasPressed": car_state.get("gasPressed", False),
          "brakePressed": car_state.get("brakePressed", False)
        }

      # Datos de GPS
      if "gpsLocationExternal" in self.sm.data and self.sm.updated["gpsLocationExternal"]:
        gps = self.sm["gpsLocationExternal"].to_dict()
        resumen["gps"] = {
          "latitude": gps.get("latitude", 0),
          "longitude": gps.get("longitude", 0),
          "altitude": gps.get("altitude", 0),
          "gps_valid": gps.get("latitude", 0) != 0 and gps.get("longitude", 0) != 0
        }

      # Datos de control
      if "carControl" in self.sm.data and self.sm.updated["carControl"]:
        car_control = self.sm["carControl"].to_dict()
        hud = car_control.get("hudControl", {})
        resumen["control"] = {
          "setSpeed": hud.get("setSpeed", 0),
          "setSpeed_kmh": hud.get("setSpeed", 0) * 3.6,
          "active": car_control.get("active", False)
        }

      # Datos de radar
      if "radarState" in self.sm.data and self.sm.updated["radarState"]:
        radar = self.sm["radarState"].to_dict()
        resumen["radar"] = {
          "dRel": radar.get("dRel", 0),
          "vRel": radar.get("vRel", 0),
          "aRel": radar.get("aRel", 0),
          "vLead": radar.get("vLead", 0),
          "hasLead": radar.get("dRel", 0) > 0
        }

      # Enviar resumen
      topic_resumen = f"telemetry_mqtt/{self.DongleID}/resumen_principal"
      self.mqttc.publish(topic_resumen, json.dumps(resumen), qos=0)
      print(f"📊 Resumen de telemetría enviado: {topic_resumen}")

    except Exception as e:
      print(f"❌ Error al enviar resumen de telemetría: {e}")

if __name__ == "__main__":
  sender = MQTTEnvioGeneral()
  sender.start()

  while not sender.conectado:
    time.sleep(0.5)

  while True:
    time.sleep(10)
