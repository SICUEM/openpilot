#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import time
import threading
import paho.mqtt.client as mqtt
from openpilot.common.params import Params
import os

class MQTTComandos:
  def __init__(self):
    self.base_path = os.path.dirname(os.path.abspath(__file__))
    self.jsonConfig = os.path.join(self.base_path, "config_mqtt.json")
    self.params = Params()
    self.DongleID = self.params.get("DongleId").decode("utf-8") if self.params.get("DongleId") else "DongleID"
    self.conectado = False
    self.stop_event = threading.Event()
    self.load_config()
    self.init_mqtt()

  def load_config(self):
    with open(self.jsonConfig, "r") as f:
      config = json.load(f)
      self.broker_address = config.get("broker", "localhost")

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
          print("✅ MQTT Comandos conectado al broker")
        break
      except Exception as e:
        print(f"❌ Error al conectar MQTT Comandos: {e}")
        time.sleep(5)

  def on_connect(self, client, userdata, flags, rc):
    if rc == 0:
      self.conectado = True
      print("🔌 MQTT Comandos conectado")
      # Suscribirse a todos los comandos del sistema AdriPilot
      topics = [
        f"telemetry_config/{self.DongleID}/left",           # Cambio carril izquierda
        f"telemetry_config/{self.DongleID}/right",          # Cambio carril derecha
        f"telemetry_config/{self.DongleID}/control",        # Control básico (forward, break, tright, tleft)
        f"telemetry_config/{self.DongleID}/speed",          # Comandos de velocidad (formato JSON)
        f"telemetry_config/{self.DongleID}/speed_up",       # Comando aumentar velocidad (formato servidor)
        f"telemetry_config/{self.DongleID}/speed_down",     # Comando disminuir velocidad (formato servidor)
        f"telemetry_config/{self.DongleID}/intervalos"      # Configuración intervalos
      ]

      for topic in topics:
        client.subscribe(topic, qos=0)

      print(f"📡 Suscrito a comandos para {self.DongleID}")
      print(f"📡 Topics suscritos:")
      for topic in topics:
        print(f"   - {topic}")
    else:
      print(f"🔌 Error conexión MQTT Comandos: {rc}")

  def on_disconnect(self, client, userdata, rc):
    self.conectado = False
    print("🔌 MQTT Comandos desconectado. Reintentando...")

  def on_message(self, client, userdata, msg):
    """Callback que maneja los mensajes MQTT de comandos."""
    try:
      topic = msg.topic
      payload = msg.payload.decode(errors="ignore").strip()

      print(f"📥 MQTT recibido: {topic} -> {payload}")

      # Comando de cambio de carril a la izquierda
      if topic.endswith("/left"):
        self.handle_lane_change_left(payload)

      # Comando de cambio de carril a la derecha
      elif topic.endswith("/right"):
        self.handle_lane_change_right(payload)

      # Comando de control básico (forward, break, tright, tleft)
      elif topic.endswith("/control"):
        self.handle_control_commands(payload)

      # Comando de velocidad (increase/decrease) - formato JSON
      elif topic.endswith("/speed"):
        self.handle_speed_commands(payload)

      # Comando de aumentar velocidad - formato servidor
      elif topic.endswith("/speed_up"):
        self.handle_speed_up_server(payload)

      # Comando de disminuir velocidad - formato servidor
      elif topic.endswith("/speed_down"):
        self.handle_speed_down_server(payload)

      # Comando de intervalos
      elif topic.endswith("/intervalos"):
        self.handle_intervalos(payload)

    except Exception as e:
      print(f"❌ Error procesando comando MQTT: {e}")

  def handle_lane_change_left(self, payload):
    """Maneja el comando de cambio de carril a la izquierda."""
    print(f"🚗 Procesando comando cambio carril IZQUIERDA para {self.DongleID}")

    # Verificar toggle de seguridad c_carril
    if not self.params.get_bool("c_carril"):
      print("🛑 Cambio de carril a IZQUIERDA bloqueado por toggle c_carril.")
      return

    if payload == "false":
      self.params.put_bool("ForceLaneChangeLeft", False)
      self.params.put_bool("ForceLaneChangeRight", False)
      print(f"🛑 Cambio de carril cancelado (left=false) para {self.DongleID}")

    elif self.params.get_bool("ForceLaneChangeRight"):
      print("⚠️ No se puede activar IZQ, ya hay cambio a DERECHA")
      self.params.put_bool("ForceLaneChangeLeft", False)
      self.params.put_bool("ForceLaneChangeRight", False)
      print(f"🛑 Ambos cancelados por conflicto IZQ-DER")
    else:
      self.params.put_bool("ForceLaneChangeLeft", True)
      print(f"✅ Ejecutando cambio de carril IZQUIERDA para {self.DongleID}")

  def handle_lane_change_right(self, payload):
    """Maneja el comando de cambio de carril a la derecha."""
    print(f"🚗 Procesando comando cambio carril DERECHA para {self.DongleID}")

    # Verificar toggle de seguridad c_carril
    if not self.params.get_bool("c_carril"):
      print("🛑 Cambio de carril a DERECHA bloqueado por toggle c_carril.")
      return

    if payload == "false":
      self.params.put_bool("ForceLaneChangeLeft", False)
      self.params.put_bool("ForceLaneChangeRight", False)
      print(f"🛑 Cambio de carril cancelado (right=false) para {self.DongleID}")

    elif self.params.get_bool("ForceLaneChangeLeft"):
      print("⚠️ No se puede activar DER, ya hay cambio a IZQUIERDA")
      self.params.put_bool("ForceLaneChangeLeft", False)
      self.params.put_bool("ForceLaneChangeRight", False)
      print(f"🛑 Ambos cancelados por conflicto DER-IZQ")
    else:
      self.params.put_bool("ForceLaneChangeRight", True)
      print(f"✅ Ejecutando cambio de carril DERECHA para {self.DongleID}")

  def handle_control_commands(self, payload):
    """Maneja los comandos de control básico (forward, break, tright, tleft)."""
    try:
      import json

      # Intentar parsear como JSON primero
      try:
        data = json.loads(payload)

        # Comando Forward (Arriba)
        if data.get("forward"):
          try:
            from openpilot.sicuem.adripilot.adripilot_control_ultra_simple import adripilot_forward
            adripilot_forward = True
            print(f"🚀 Comando FORWARD activado para {self.DongleID}")
          except ImportError:
            self.params.put_bool("adripilot_forward", True)
            print(f"🚀 Comando FORWARD activado para {self.DongleID} (fallback a Params)")

        # Comando Break (Abajo)
        if data.get("break"):
          try:
            from openpilot.sicuem.adripilot.adripilot_control_ultra_simple import adripilot_break
            adripilot_break = True
            print(f"🛑 Comando BREAK activado para {self.DongleID}")
          except ImportError:
            self.params.put_bool("adripilot_break", True)
            print(f"🛑 Comando BREAK activado para {self.DongleID} (fallback a Params)")

        # Comando Tright (Derecha) - formato JSON
        if data.get("tright"):
          # Activar giro temporal usando el nuevo sistema
          try:
            from openpilot.sicuem.adripilot.adripilot_steering_pulse import set_steering_pulse
            set_steering_pulse("right")
            print(f"↗️ Comando TRIGHT (JSON) activado para {self.DongleID} - giro temporal a la derecha")
          except Exception as e:
            print(f"❌ Error activando giro temporal TRIGHT: {e}")
          # Mantener compatibilidad con código viejo (opcional)
          try:
            from openpilot.sicuem.adripilot.adripilot_control_ultra_simple import adripilot_tright
            adripilot_tright = True
          except ImportError:
            pass

        # Comando Tleft (Izquierda) - formato JSON
        if data.get("tleft"):
          # Activar giro temporal usando el nuevo sistema
          try:
            from openpilot.sicuem.adripilot.adripilot_steering_pulse import set_steering_pulse
            set_steering_pulse("left")
            print(f"↖️ Comando TLEFT (JSON) activado para {self.DongleID} - giro temporal a la izquierda")
          except Exception as e:
            print(f"❌ Error activando giro temporal TLEFT: {e}")
          # Mantener compatibilidad con código viejo (opcional)
          try:
            from openpilot.sicuem.adripilot.adripilot_control_ultra_simple import adripilot_tleft
            adripilot_tleft = True
          except ImportError:
            pass

      except json.JSONDecodeError:
        # Si no es JSON, tratar como string simple (formato servidor: "tleft" o "tright")
        payload_lower = payload.lower().strip()

        if payload_lower == "tright":
          # Activar giro temporal a la derecha usando variables globales
          try:
            from openpilot.sicuem.adripilot.adripilot_steering_pulse import set_steering_pulse
            set_steering_pulse("right")
            print(f"↗️ Comando TRIGHT (string) activado para {self.DongleID} - giro temporal a la derecha")
          except Exception as e:
            print(f"❌ Error activando giro temporal TRIGHT: {e}")

        elif payload_lower == "tleft":
          # Activar giro temporal a la izquierda usando variables globales
          try:
            from openpilot.sicuem.adripilot.adripilot_steering_pulse import set_steering_pulse
            set_steering_pulse("left")
            print(f"↖️ Comando TLEFT (string) activado para {self.DongleID} - giro temporal a la izquierda")
          except Exception as e:
            print(f"❌ Error activando giro temporal TLEFT: {e}")

        else:
          print(f"⚠️ Comando de control no reconocido (string): '{payload}'")

    except Exception as e:
      print(f"❌ Error procesando comando de control: {e}")

  def handle_speed_commands(self, payload):
    """Maneja los comandos de velocidad (increase/decrease) - formato JSON."""
    try:
      import json
      data = json.loads(payload)

      # Aumentar velocidad
      if data.get("speed_increase"):
        try:
          from openpilot.sicuem.adripilot.adripilot_speed_ultra_simple import adripilot_speed_increase
          adripilot_speed_increase = True
          print(f"⬆️ Comando SPEED INCREASE activado para {self.DongleID}")
        except ImportError:
          self.params.put_bool("adripilot_speed_increase", True)
          print(f"⬆️ Comando SPEED INCREASE activado para {self.DongleID} (fallback a Params)")

      # Reducir velocidad
      if data.get("speed_decrease"):
        try:
          from openpilot.sicuem.adripilot.adripilot_speed_ultra_simple import adripilot_speed_decrease
          adripilot_speed_decrease = True
          print(f"⬇️ Comando SPEED DECREASE activado para {self.DongleID}")
        except ImportError:
          self.params.put_bool("adripilot_speed_decrease", True)
          print(f"⬇️ Comando SPEED DECREASE activado para {self.DongleID} (fallback a Params)")

    except json.JSONDecodeError:
      print(f"❌ Error al decodificar comando de velocidad: {payload}")
    except Exception as e:
      print(f"❌ Error procesando comando de velocidad: {e}")

  def handle_speed_up_server(self, payload):
    """Maneja el comando de aumentar velocidad - formato servidor."""
    try:
      # El servidor puede enviar "+1" o "1" como string
      if payload in ["+1", "1"]:
        # Usar variable global del sistema ultra simplificado
        try:
          from openpilot.sicuem.adripilot.adripilot_speed_ultra_simple import adripilot_speed_increase
          adripilot_speed_increase = True
          print(f"⬆️ Comando SPEED UP ({payload}) activado para {self.DongleID}")
        except ImportError:
          # Fallback: usar parámetros como respaldo
          self.params.put_bool("adripilot_speed_increase", True)
          print(f"⬆️ Comando SPEED UP ({payload}) activado para {self.DongleID} (fallback a Params)")
      else:
        print(f"⚠️ Comando SPEED UP no reconocido: {payload}")

    except Exception as e:
      print(f"❌ Error procesando comando SPEED UP: {e}")

  def handle_speed_down_server(self, payload):
    """Maneja el comando de disminuir velocidad - formato servidor."""
    try:
      # El servidor puede enviar "-1" o "1" como string
      if payload in ["-1", "1"]:
        # Usar variable global del sistema ultra simplificado
        try:
          from openpilot.sicuem.adripilot.adripilot_speed_ultra_simple import adripilot_speed_decrease
          adripilot_speed_decrease = True
          print(f"⬇️ Comando SPEED DOWN ({payload}) activado para {self.DongleID}")
        except ImportError:
          # Fallback: usar parámetros como respaldo
          self.params.put_bool("adripilot_speed_decrease", True)
          print(f"⬇️ Comando SPEED DOWN ({payload}) activado para {self.DongleID} (fallback a Params)")
      else:
        print(f"⚠️ Comando SPEED DOWN no reconocido: {payload}")

    except Exception as e:
      print(f"❌ Error procesando comando SPEED DOWN: {e}")

  def handle_intervalos(self, payload):
    """Maneja el comando de intervalos."""
    try:
      import json
      data = json.loads(payload)

      if data.get("intervalos_toggle") == "true":
        self.params.put_bool("intervalos_toggle", True)
        print(f"✅ intervalos_toggle activado para {self.DongleID}")
      elif data.get("intervalos_toggle") == "false":
        self.params.put_bool("intervalos_toggle", False)
        print(f"🛑 intervalos_toggle desactivado para {self.DongleID}")
      else:
        # Compatibilidad con formato anterior
        if payload.lower() == "true":
          self.params.put_bool("intervalos_toggle", True)
          print(f"✅ intervalos_toggle activado para {self.DongleID}")
        elif payload.lower() == "false":
          self.params.put_bool("intervalos_toggle", False)
          print(f"🛑 intervalos_toggle desactivado para {self.DongleID}")
        else:
          print(f"⚠️ Valor no reconocido en intervalos: '{payload}'")
    except json.JSONDecodeError:
      # Fallback para formato simple
      if payload.lower() == "true":
        self.params.put_bool("intervalos_toggle", True)
        print(f"✅ intervalos_toggle activado para {self.DongleID}")
      elif payload.lower() == "false":
        self.params.put_bool("intervalos_toggle", False)
        print(f"🛑 intervalos_toggle desactivado para {self.DongleID}")
      else:
        print(f"⚠️ Valor no reconocido en intervalos: '{payload}'")
    except Exception as e:
      print(f"❌ Error procesando comando de intervalos: {e}")

  def start(self):
    """Inicia el cliente MQTT de comandos."""
    print("🚀 Iniciando MQTT Comandos...")
    # El cliente ya se inicia automáticamente en el hilo

  def stop(self):
    """Detiene el cliente MQTT de comandos."""
    self.stop_event.set()
    self.mqttc.disconnect()
    print("🛑 MQTT Comandos detenido")

if __name__ == "__main__":
  comandos = MQTTComandos()
  comandos.start()

  try:
    while True:
      time.sleep(1)
  except KeyboardInterrupt:
    comandos.stop()

