#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para enviar imágenes de las cámaras del Comma al servidor AdriPilot mediante MQTT.
Usa el thumbnail JPEG nativo generado por camerad (cereal 'thumbnail') para evitar
operaciones pesadas de CPU (VisionIPC, numpy, PIL) que causaban "Camera Frame Rate Low".
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


class CameraSender:
  """Envía imágenes de las cámaras al servidor mediante MQTT usando el thumbnail nativo de camerad."""

  def __init__(self, mqtt_client, dongle_id, camera_type="road", interval_seconds=5.0):
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
    self.last_sent = 0
    self.frame_count = 0
    self.error_count = 0
    self.consecutive_errors = 0
    self.max_backoff = 60.0

    self.params = Params()
    self.debug_enabled = False
    self._last_debug_check = 0

  def _log_debug(self, message):
    """Escribe un mensaje en el fichero de debug si modo_debug está activo."""
    try:
      now = time.time()
      if now - self._last_debug_check > 2.0:
        self.debug_enabled = self.params.get_bool("modo_debug")
        self._last_debug_check = now
      if not self.debug_enabled:
        return
      ts = time.strftime("%H:%M:%S", time.localtime())
      topic = f"telemetry_mqtt/{self.dongle_id}/camera/{self.camera_type}"
      entry = f"[{ts}] {topic}\n{message}"
      with open(DEBUG_FILE, 'a', encoding='utf-8') as f:
        f.write("\n\n" + entry)
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
    sm = messaging.SubMaster(['thumbnail'])

    cloudlog.info("CameraSender: started, waiting for thumbnail messages")

    while not self.stop_event.is_set():
      sm.update(timeout=1000)

      if not sm.updated['thumbnail']:
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
        thumb = sm['thumbnail']
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
