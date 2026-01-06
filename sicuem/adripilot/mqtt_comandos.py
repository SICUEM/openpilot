#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import time
import threading
import paho.mqtt.client as mqtt
from openpilot.common.params import Params
import os

# Importar el módulo de velocidad una sola vez al inicio para evitar problemas de importación
try:
  import openpilot.sicuem.adripilot.adripilot_speed_ultra_simple as speed_module
  SPEED_MODULE_AVAILABLE = True
except ImportError:
  SPEED_MODULE_AVAILABLE = False

class MQTTComandos:
  def __init__(self):
    self.base_path = os.path.dirname(os.path.abspath(__file__))
    self.jsonConfig = os.path.join(self.base_path, "config_mqtt.json")
    self.params = Params()
    self.DongleID = self.params.get("DongleId").decode("utf-8") if self.params.get("DongleId") else "DongleID"
    self.conectado = False
    self.stop_event = threading.Event()
    # Archivo para guardar mensajes MQTT para modo debug
    self.debug_file = "/tmp/mqtt_debug_messages.txt"
    self.max_messages = 50  # Máximo de mensajes a guardar
    self.messages_lock = threading.Lock()
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
          # print("✅ MQTT Comandos conectado al broker")  # Comentado para reducir uso de memoria
        break
      except Exception as e:
        # print(f"❌ Error al conectar MQTT Comandos: {e}")  # Comentado para reducir uso de memoria
        time.sleep(5)

  def on_connect(self, client, userdata, flags, rc):
    if rc == 0:
      self.conectado = True
      # Suscribirse a todos los comandos del sistema AdriPilot
      topics = [
        f"telemetry_config/{self.DongleID}/left",           # Cambio carril izquierda
        f"telemetry_config/{self.DongleID}/right",          # Cambio carril derecha
        f"telemetry_config/{self.DongleID}/control",        # Control básico (forward, break, tright, tleft)
        f"telemetry_config/{self.DongleID}/speed",          # Comandos de velocidad (formato JSON)
        f"telemetry_config/{self.DongleID}/speed_up",       # Comando aumentar velocidad (formato servidor)
        f"telemetry_config/{self.DongleID}/speed_down",     # Comando disminuir velocidad (formato servidor)
        f"telemetry_config/{self.DongleID}/speed_increment", # Configuración del incremento de velocidad (futuro)
        f"telemetry_config/{self.DongleID}/intervalos"      # Configuración intervalos
      ]

      for topic in topics:
        client.subscribe(topic, qos=0)

  def on_disconnect(self, client, userdata, rc):
    self.conectado = False
    # print("🔌 MQTT Comandos desconectado. Reintentando...")  # Comentado para reducir uso de memoria

  def save_debug_message(self, topic, payload):
    """Guarda un mensaje MQTT para el modo debug."""
    try:
      timestamp = time.strftime("%H:%M:%S", time.localtime())
      # Truncar payload si es muy largo
      payload_display = payload[:100] if len(payload) > 100 else payload
      message = f"[{timestamp}] {topic}\n{payload_display}\n"

      with self.messages_lock:
        # Leer mensajes existentes
        messages = []
        if os.path.exists(self.debug_file):
          try:
            with open(self.debug_file, 'r', encoding='utf-8') as f:
              content = f.read()
              # Dividir por líneas y mantener solo los últimos max_messages
              lines = content.split('\n')
              # Agrupar en mensajes (cada mensaje tiene 2 líneas: timestamp+topic y payload)
              i = 0
              while i < len(lines):
                if lines[i].startswith('['):
                  if i + 1 < len(lines):
                    messages.append(lines[i] + '\n' + lines[i + 1])
                    i += 2
                  else:
                    i += 1
                else:
                  i += 1
          except Exception:
            messages = []

        # Agregar nuevo mensaje
        messages.append(message.strip())

        # Mantener solo los últimos max_messages
        if len(messages) > self.max_messages:
          messages = messages[-self.max_messages:]

        # Escribir de vuelta
        with open(self.debug_file, 'w', encoding='utf-8') as f:
          f.write('\n\n'.join(messages))
    except Exception:
      pass  # Silenciar errores para no afectar el flujo principal

  def on_message(self, client, userdata, msg):
    """Callback que maneja los mensajes MQTT de comandos."""
    try:
      topic = msg.topic
      payload = msg.payload.decode(errors="ignore").strip()

      # Guardar mensaje para modo debug
      self.save_debug_message(topic, payload)

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

      # Comando de configuración del incremento de velocidad (para el futuro)
      elif topic.endswith("/speed_increment"):
        self.handle_speed_increment_config(payload)

      # Comando de intervalos
      elif topic.endswith("/intervalos"):
        self.handle_intervalos(payload)

    except Exception:
      pass  # Error silenciado para reducir uso de memoria

  def handle_lane_change_left(self, payload):
    """Maneja el comando de cambio de carril a la izquierda."""
    # Verificar toggle de seguridad c_carril
    if not self.params.get_bool("c_carril"):
      return

    if payload == "false":
      self.params.put_bool("ForceLaneChangeLeft", False)
      self.params.put_bool("ForceLaneChangeRight", False)
    elif self.params.get_bool("ForceLaneChangeRight"):
      self.params.put_bool("ForceLaneChangeLeft", False)
      self.params.put_bool("ForceLaneChangeRight", False)
    else:
      self.params.put_bool("ForceLaneChangeLeft", True)

  def handle_lane_change_right(self, payload):
    """Maneja el comando de cambio de carril a la derecha."""
    # Verificar toggle de seguridad c_carril
    if not self.params.get_bool("c_carril"):
      return

    if payload == "false":
      self.params.put_bool("ForceLaneChangeLeft", False)
      self.params.put_bool("ForceLaneChangeRight", False)
    elif self.params.get_bool("ForceLaneChangeLeft"):
      self.params.put_bool("ForceLaneChangeLeft", False)
      self.params.put_bool("ForceLaneChangeRight", False)
    else:
      self.params.put_bool("ForceLaneChangeRight", True)

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
          except ImportError:
            self.params.put_bool("adripilot_forward", True)

        # Comando Break (Abajo)
        if data.get("break"):
          try:
            from openpilot.sicuem.adripilot.adripilot_control_ultra_simple import adripilot_break
            adripilot_break = True
          except ImportError:
            self.params.put_bool("adripilot_break", True)

        # Comando Tright (Derecha) - formato JSON
        if data.get("tright"):
          # Activar giro temporal usando el nuevo sistema
          try:
            from openpilot.sicuem.adripilot.adripilot_steering_pulse import set_steering_pulse
            set_steering_pulse("right")
          except Exception as e:
            pass  # Error silenciado para reducir uso de memoria
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
          except Exception as e:
            pass  # Error silenciado para reducir uso de memoria
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
          except Exception as e:
            pass  # Error silenciado para reducir uso de memoria

        elif payload_lower == "tleft":
          # Activar giro temporal a la izquierda usando variables globales
          try:
            from openpilot.sicuem.adripilot.adripilot_steering_pulse import set_steering_pulse
            set_steering_pulse("left")
          except Exception as e:
            pass  # Error silenciado para reducir uso de memoria

    except Exception:
      pass  # Error silenciado para reducir uso de memoria

  def handle_speed_commands(self, payload):
    """Maneja los comandos de velocidad (increase/decrease) - formato JSON.

    IMPORTANTE: Solo funciona cuando el control longitudinal está activo (crucero activado).
    """
    try:
      import json
      data = json.loads(payload)

      # Aumentar velocidad
      if data.get("speed_increase"):
        if SPEED_MODULE_AVAILABLE:
          speed_module.adripilot_speed_increase = True
        else:
          self.params.put_bool("adripilot_speed_increase", True)

      # Reducir velocidad
      if data.get("speed_decrease"):
        if SPEED_MODULE_AVAILABLE:
          speed_module.adripilot_speed_decrease = True
        else:
          self.params.put_bool("adripilot_speed_decrease", True)

    except json.JSONDecodeError:
      pass  # Error silenciado para reducir uso de memoria
    except Exception:
      pass  # Error silenciado para reducir uso de memoria

  def handle_speed_up_server(self, payload):
    """Maneja el comando de aumentar velocidad - formato servidor/app.

    El servidor/app envía el comando cuando el usuario pulsa el botón "Aumentar".
    Formatos aceptados:
    - JSON: {'speed_up': true, 'timestamp': ...} (nuevo formato desde app)
    - String: "1", "+1", o cualquier string (formato antiguo del servidor)

    IMPORTANTE: Solo funciona cuando el control longitudinal está activo (crucero activado).
    """
    try:
      # Intentar parsear como JSON primero (nuevo formato desde app)
      try:
        data = json.loads(payload)
        if data.get("speed_up") is True:
          # Formato nuevo: JSON con speed_up: true
          if SPEED_MODULE_AVAILABLE:
            speed_module.adripilot_speed_increase = True
          else:
            self.params.put_bool("adripilot_speed_increase", True)
          return
      except (json.JSONDecodeError, AttributeError):
        # No es JSON, tratar como string (formato antiguo del servidor)
        # Aceptamos cualquier payload como válido para mantener compatibilidad
        if SPEED_MODULE_AVAILABLE:
          speed_module.adripilot_speed_increase = True
        else:
          self.params.put_bool("adripilot_speed_increase", True)

    except Exception:
      pass  # Error silenciado para reducir uso de memoria

  def handle_speed_down_server(self, payload):
    """Maneja el comando de disminuir velocidad - formato servidor/app.

    El servidor/app envía el comando cuando el usuario pulsa el botón "Disminuir".
    Formatos aceptados:
    - JSON: {'speed_down': true, 'timestamp': ...} (nuevo formato desde app)
    - String: "1", "-1", o cualquier string (formato antiguo del servidor)

    IMPORTANTE: Solo funciona cuando el control longitudinal está activo (crucero activado).
    """
    try:
      # Intentar parsear como JSON primero (nuevo formato desde app)
      try:
        data = json.loads(payload)
        if data.get("speed_down") is True:
          # Formato nuevo: JSON con speed_down: true
          if SPEED_MODULE_AVAILABLE:
            speed_module.adripilot_speed_decrease = True
          else:
            self.params.put_bool("adripilot_speed_decrease", True)
          return
      except (json.JSONDecodeError, AttributeError):
        # No es JSON, tratar como string (formato antiguo del servidor)
        # Aceptamos cualquier payload como válido para mantener compatibilidad
        if SPEED_MODULE_AVAILABLE:
          speed_module.adripilot_speed_decrease = True
        else:
          self.params.put_bool("adripilot_speed_decrease", True)

    except Exception:
      pass  # Error silenciado para reducir uso de memoria

  def handle_speed_increment_config(self, payload):
    """Maneja la configuración del incremento de velocidad desde la app.

    La app puede enviar el valor del incremento en km/h (ej: "10", "5", "20").
    Este valor se guarda en Params y será usado por el sistema de control de velocidad.

    Formato esperado: número como string (ej: "10" para 10 km/h)
    Rango válido: 1-50 km/h
    """
    try:
      increment = float(payload.strip())
      # Validar rango (1-50 km/h)
      if 1.0 <= increment <= 50.0:
        self.params.put("adripilot_speed_increment", str(increment))
    except (ValueError, Exception):
      pass  # Error silenciado para reducir uso de memoria

  def handle_intervalos(self, payload):
    """Maneja el comando de intervalos."""
    try:
      import json
      data = json.loads(payload)

      if data.get("intervalos_toggle") == "true":
        self.params.put_bool("intervalos_toggle", True)
      elif data.get("intervalos_toggle") == "false":
        self.params.put_bool("intervalos_toggle", False)
      else:
        # Compatibilidad con formato anterior
        if payload.lower() == "true":
          self.params.put_bool("intervalos_toggle", True)
        elif payload.lower() == "false":
          self.params.put_bool("intervalos_toggle", False)
    except json.JSONDecodeError:
      # Fallback para formato simple
      if payload.lower() == "true":
        self.params.put_bool("intervalos_toggle", True)
      elif payload.lower() == "false":
        self.params.put_bool("intervalos_toggle", False)
    except Exception:
      pass  # Error silenciado para reducir uso de memoria

  def start(self):
    """Inicia el cliente MQTT de comandos."""
    # El cliente ya se inicia automáticamente en el hilo

  def stop(self):
    """Detiene el cliente MQTT de comandos."""
    self.stop_event.set()
    self.mqttc.disconnect()

if __name__ == "__main__":
  comandos = MQTTComandos()
  comandos.start()

  try:
    while True:
      time.sleep(1)
  except KeyboardInterrupt:
    comandos.stop()

