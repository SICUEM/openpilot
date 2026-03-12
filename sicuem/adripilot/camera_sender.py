#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para enviar imágenes de las cámaras del Comma al servidor AdriPilot mediante MQTT.
Usa el thumbnail JPEG nativo generado por camerad (cereal 'thumbnail') para evitar
operaciones pesadas de CPU (VisionIPC, numpy, PIL) que causaban "Camera Frame Rate Low".

Soporta control remoto desde la app ADRIPILOT via MQTT:
- Activar/desactivar envio de imagenes
- Cambiar frecuencia de envio (1s, 2s, 5s, 10s, 30s, 60s)
- Persistencia de configuracion en /data/adripilot_camera_config.json
"""
import time
import threading
import base64
import json
import os

import cereal.messaging as messaging
from openpilot.common.params import Params
from openpilot.common.swaglog import cloudlog

DEBUG_FILE = "/tmp/mqtt_debug_messages.txt"
CAMERA_CONFIG_FILE = "/data/adripilot_camera_config.json"
VALID_FREQUENCIES = [1, 2, 5, 10, 30, 60]


class CameraSender:
  """Envía imágenes de las cámaras al servidor mediante MQTT usando el thumbnail nativo de camerad."""

  def __init__(self, mqtt_client, dongle_id, camera_type="road", interval_seconds=2.0):
    """
    Inicializa el envío de imágenes de cámara.

    Args:
      mqtt_client: Cliente MQTT compartido (paho.mqtt.client.Client)
      dongle_id: ID del dispositivo
      camera_type: Tipo de cámara ("road", "driver", "wide")
      interval_seconds: Intervalo entre envíos (segundos)
    """
    self.mqtt_client = mqtt_client
    self.dongle_id = dongle_id
    self.camera_type = camera_type
    self.interval_seconds = interval_seconds

    self.stop_event = threading.Event()
    self.sending_enabled = False  # Control remoto: desactivado por defecto
    self.last_sent = 0
    self.frame_count = 0
    self.error_count = 0
    self.consecutive_errors = 0
    self.max_backoff = 60.0

    self.params = Params()
    self.debug_enabled = False
    self._last_debug_check = 0

    # Mapeo de camera_type a canal cereal para thumbnails
    self._thumbnail_channels = {
      'road': 'thumbnail',
      'driver': 'driverThumbnail',
      'wide': 'thumbnail',
    }

    # Cargar configuracion persistida (si existe)
    self._load_config()

  def _load_config(self):
    """Carga configuracion de camara desde archivo persistido."""
    try:
      if os.path.exists(CAMERA_CONFIG_FILE):
        with open(CAMERA_CONFIG_FILE, 'r') as f:
          config = json.load(f)
        if "image_sending_enabled" in config:
          self.sending_enabled = bool(config["image_sending_enabled"])
        if "send_frequency_seconds" in config:
          freq = int(config["send_frequency_seconds"])
          if freq in VALID_FREQUENCIES:
            self.interval_seconds = float(freq)
        if "camera_type" in config:
          ct = config["camera_type"]
          if ct in ("road", "driver", "wide"):
            self.camera_type = ct
        cloudlog.info(f"CameraSender: config loaded - enabled={self.sending_enabled}, freq={self.interval_seconds}s, type={self.camera_type}")
    except Exception as e:
      cloudlog.warning(f"CameraSender: could not load config, using defaults: {e}")

  def _save_config(self):
    """Persiste configuracion de camara a disco para sobrevivir reinicios."""
    try:
      config = {
        "image_sending_enabled": self.sending_enabled,
        "send_frequency_seconds": int(self.interval_seconds),
        "camera_type": self.camera_type,
      }
      with open(CAMERA_CONFIG_FILE, 'w') as f:
        json.dump(config, f)
    except Exception as e:
      cloudlog.warning(f"CameraSender: could not save config: {e}")

  def set_enabled(self, enabled):
    """Activa o desactiva el envio de imagenes (control remoto desde app)."""
    self.sending_enabled = bool(enabled)
    self._save_config()
    cloudlog.info(f"CameraSender: sending {'enabled' if self.sending_enabled else 'disabled'}")

  def set_frequency(self, seconds):
    """Cambia la frecuencia de envio de imagenes (control remoto desde app)."""
    seconds = int(seconds)
    if seconds in VALID_FREQUENCIES:
      self.interval_seconds = float(seconds)
      self._save_config()
      cloudlog.info(f"CameraSender: frequency changed to {seconds}s")
    else:
      cloudlog.warning(f"CameraSender: invalid frequency {seconds}s, valid: {VALID_FREQUENCIES}")

  def apply_config(self, config_data):
    """Aplica configuracion recibida por MQTT desde la app.

    Args:
      config_data: dict con campos opcionales:
        - image_sending_enabled: bool
        - send_frequency_seconds: int (1, 2, 5, 10, 30, 60)
        - save_images: bool (informativo, no afecta al comma)
    """
    changed = False
    if "image_sending_enabled" in config_data:
      self.sending_enabled = bool(config_data["image_sending_enabled"])
      changed = True
    if "send_frequency_seconds" in config_data:
      freq = int(config_data["send_frequency_seconds"])
      if freq in VALID_FREQUENCIES:
        self.interval_seconds = float(freq)
        changed = True
    if "camera_type" in config_data:
      ct = config_data["camera_type"]
      if ct in ("road", "driver", "wide"):
        self.camera_type = ct
        changed = True
    if changed:
      self._save_config()
      cloudlog.info(f"CameraSender: config updated - enabled={self.sending_enabled}, freq={self.interval_seconds}s, type={self.camera_type}")

  def _log_debug(self, message):
    """Escribe/actualiza un mensaje de cámara en el fichero de debug si modo_debug está activo.
    En lugar de añadir una nueva línea cada vez, actualiza la entrada existente de cámara."""
    try:
      now = time.time()
      if now - self._last_debug_check > 2.0:
        self.debug_enabled = self.params.get_bool("modo_debug")
        self._last_debug_check = now
      if not self.debug_enabled:
        return
      ts = time.strftime("%H:%M:%S", time.localtime())
      topic = f"telemetry_mqtt/{self.dongle_id}/camera/{self.camera_type}"
      new_entry = f"[{ts}] {topic}\n{message}"

      # Leer contenido existente y reemplazar la entrada de cámara si ya existe
      entries = []
      camera_marker = f"/camera/{self.camera_type}"
      found = False
      if os.path.exists(DEBUG_FILE):
        try:
          with open(DEBUG_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
          if content.strip():
            entries = [e.strip() for e in content.split("\n\n") if e.strip()]
            for i, entry in enumerate(entries):
              if camera_marker in entry:
                entries[i] = new_entry
                found = True
                break
        except Exception:
          entries = []

      if not found:
        entries.append(new_entry)

      try:
        with open(DEBUG_FILE, 'w', encoding='utf-8') as f:
          f.write("\n\n".join(entries))
      except Exception:
        pass
    except Exception:
      pass

  def send_image(self, jpeg_data, frame_id, timestamp):
    """Envía imagen por MQTT usando el cliente compartido."""
    try:
      jpeg_base64 = base64.b64encode(jpeg_data).decode('utf-8')

      payload = {
        "dongle_id": self.dongle_id,
        "camera_type": self.camera_type,
        "frame_id": frame_id,
        "timestamp": timestamp,
        "image": jpeg_base64,
        "size_bytes": len(jpeg_data),
      }

      topic = f"telemetry_mqtt/{self.dongle_id}/camera/{self.camera_type}"

      result = self.mqtt_client.publish(topic, json.dumps(payload), qos=0)
      if result.rc != 0:
        cloudlog.warning(f"CameraSender: MQTT publish failed rc={result.rc}")
        self.error_count += 1
        self.consecutive_errors += 1
        return False

      self.frame_count += 1
      self.consecutive_errors = 0
      self._log_debug(f"Imagen enviada frame={frame_id} size={len(jpeg_data)}B")
      cloudlog.debug(f"CameraSender: sent frame {frame_id} ({len(jpeg_data)} bytes)")
      return True
    except Exception as e:
      cloudlog.error(f"CameraSender: send_image error: {e}")
      self.error_count += 1
      self.consecutive_errors += 1
      return False

  def run(self):
    """Loop principal: lee thumbnail nativo de camerad y envía por MQTT."""
    channel = self._thumbnail_channels.get(self.camera_type, 'thumbnail')
    sm = messaging.SubMaster([channel])

    cloudlog.info(f"CameraSender: started on channel '{channel}' (camera_type={self.camera_type})")

    while not self.stop_event.is_set():
      sm.update(timeout=1000)

      if not sm.updated[channel]:
        continue

      # Si el envio esta desactivado por la app, no procesar
      if not self.sending_enabled:
        continue

      current_time = time.time()

      # Backoff exponencial si hay errores consecutivos
      if self.consecutive_errors > 0:
        backoff = min(self.max_backoff, 2.0 ** min(self.consecutive_errors, 6))
        effective_interval = self.interval_seconds + backoff
      else:
        effective_interval = self.interval_seconds

      # Verificar intervalo
      if current_time - self.last_sent < effective_interval:
        continue

      try:
        thumb = sm[channel]
        jpeg_data = thumb.thumbnail
        frame_id = thumb.frameId

        if not jpeg_data:
          cloudlog.warning("CameraSender: received empty thumbnail")
          continue

        timestamp_ms = int(current_time * 1000)
        self.send_image(jpeg_data, frame_id, timestamp_ms)
        self.last_sent = current_time

      except Exception as e:
        cloudlog.error(f"CameraSender: error processing thumbnail: {e}")
        self.error_count += 1
        self.consecutive_errors += 1

  def start(self):
    """Inicia el thread de captura."""
    if not self.stop_event.is_set():
      self.thread = threading.Thread(target=self.run, daemon=True, name=f"CameraSender-{self.camera_type}")
      self.thread.start()
      return True
    return False

  def stop(self):
    """Detiene el capturador."""
    self.stop_event.set()
    if hasattr(self, 'thread'):
      self.thread.join(timeout=5)
