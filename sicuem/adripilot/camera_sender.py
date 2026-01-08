#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para enviar imágenes de las cámaras del Comma al servidor AdriPilot mediante MQTT.
Configurado para calidad baja y frame rate alto sin saturar el sistema.
"""
import time
import threading
import base64
import json
import io
import os
import numpy as np
from PIL import Image
from msgq.visionipc import VisionIpcClient, VisionStreamType
import cereal.messaging as messaging
import paho.mqtt.publish as publish
from openpilot.common.params import Params
from openpilot.common.realtime import DT_MDL

# Detectar si estamos en modo simulación
SIMULATION = "SIMULATION" in os.environ

class CameraSender:
  """Envía imágenes de las cámaras al servidor mediante MQTT."""

  def __init__(self, camera_type="road", interval_seconds=2.0, thumbnail_size=(320, 180), quality=35):
    """
    Inicializa el envío de imágenes de cámara.

    Args:
      camera_type: Tipo de cámara ("road", "driver", "wide")
      interval_seconds: Intervalo entre envíos (segundos)
      thumbnail_size: Tamaño del thumbnail (ancho, alto)
      quality: Calidad JPEG (1-100, más bajo = más compresión)
    """
    self.camera_type = camera_type
    self.interval_seconds = interval_seconds
    self.thumbnail_size = thumbnail_size
    self.quality = quality
    self.params = Params()
    self.dongle_id = self.params.get("DongleId").decode("utf-8") if self.params.get("DongleId") else "UnregisteredDevice"

    # Cargar configuración MQTT
    base_path = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_path, "config_mqtt.json")
    try:
      with open(config_path, "r") as f:
        config = json.load(f)
        self.broker = config.get("broker", "localhost")
        self.port = config.get("broker_port", 1883)
    except Exception:
      self.broker = "localhost"
      self.port = 1883

    # Mapeo de tipos de cámara
    self.stream_map = {
      "road": ("roadCameraState", VisionStreamType.VISION_STREAM_ROAD),
      "driver": ("driverCameraState", VisionStreamType.VISION_STREAM_DRIVER),
      "wide": ("wideRoadCameraState", VisionStreamType.VISION_STREAM_WIDE_ROAD),
    }

    if camera_type not in self.stream_map:
      raise ValueError(f"Tipo de cámara inválido: {camera_type}. Debe ser 'road', 'driver' o 'wide'")

    self.stop_event = threading.Event()
    self.last_sent = 0
    self.frame_count = 0
    self.error_count = 0

  def yuv_to_rgb(self, y, u, v):
    """Convierte YUV420 a RGB."""
    # Repetir U y V para coincidir con el tamaño de Y
    ul = np.repeat(np.repeat(u, 2).reshape(u.shape[0], y.shape[1]), 2, axis=0).reshape(y.shape)
    vl = np.repeat(np.repeat(v, 2).reshape(v.shape[0], y.shape[1]), 2, axis=0).reshape(y.shape)

    # Convertir a formato YUV completo
    yuv = np.dstack((y, ul, vl)).astype(np.int16)
    yuv[:, :, 1:] -= 128

    # Matriz de conversión YUV a RGB
    m = np.array([
      [1.00000,  1.00000, 1.00000],
      [0.00000, -0.39465, 2.03211],
      [1.13983, -0.58060, 0.00000],
    ])
    rgb = np.dot(yuv, m).clip(0, 255)
    return rgb.astype(np.uint8)

  def extract_image(self, buf):
    """Extrae imagen RGB del buffer VisionIPC."""
    try:
      # Extraer plano Y (formato NV12: Y plano completo, luego UV intercalado)
      y = np.array(buf.data[:buf.uv_offset], dtype=np.uint8).reshape((-1, buf.stride))[:buf.height, :buf.width]

      # Extraer planos U y V (intercalados en formato NV12)
      # En NV12: uv_offset apunta al inicio de los datos UV intercalados
      uv_data = buf.data[buf.uv_offset:]
      u = np.array(uv_data[::2], dtype=np.uint8).reshape((-1, buf.stride//2))[:buf.height//2, :buf.width//2]
      v = np.array(uv_data[1::2], dtype=np.uint8).reshape((-1, buf.stride//2))[:buf.height//2, :buf.width//2]

      return self.yuv_to_rgb(y, u, v)
    except Exception:
      return None

  def rgb_to_jpeg(self, rgb_array):
    """Convierte array RGB a JPEG comprimido."""
    try:
      img = Image.fromarray(rgb_array)

      # Redimensionar a thumbnail manteniendo aspecto
      img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)

      # Convertir a JPEG
      img_bytes = io.BytesIO()
      img.save(img_bytes, format='JPEG', quality=self.quality, optimize=True)
      return img_bytes.getvalue()
    except Exception:
      return None

  def send_image(self, jpeg_data, frame_id, timestamp):
    """Envía imagen por MQTT."""
    try:
      # Convertir a base64
      jpeg_base64 = base64.b64encode(jpeg_data).decode('utf-8')

      # Payload JSON
      payload = {
        "dongle_id": self.dongle_id,
        "camera_type": self.camera_type,
        "frame_id": frame_id,
        "timestamp": timestamp,
        "image": jpeg_base64,
        "size_bytes": len(jpeg_data),
        "resolution": {
          "width": self.thumbnail_size[0],
          "height": self.thumbnail_size[1]
        },
        "quality": self.quality
      }

      topic = f"telemetry_mqtt/{self.dongle_id}/camera/{self.camera_type}"

      # Enviar por MQTT (QoS 0 para máximo rendimiento)
      publish.single(
        topic,
        json.dumps(payload),
        hostname=self.broker,
        port=self.port,
        qos=0
      )

      self.frame_count += 1
      return True
    except Exception:
      self.error_count += 1
      return False

  def run(self):
    """Loop principal de captura y envío."""
    # Verificar si estamos en simulador
    if SIMULATION:
      # Intentar conectar de todas formas por si el simulador tiene cámaras
      # pero con un timeout más corto
      pass

    msg_name, stream_type = self.stream_map[self.camera_type]

    # Inicializar VisionIPC
    sm = messaging.SubMaster([msg_name])
    vipc_client = VisionIpcClient("camerad", stream_type, True)

    # Esperar a que camerad esté listo (máximo 10 segundos, 5 en simulador)
    wait_timeout = 5.0 if SIMULATION else 10.0
    start_wait = time.time()
    while not self.stop_event.is_set() and (time.time() - start_wait) < wait_timeout:
      sm.update(timeout=0.1)
      if sm[msg_name].frameId > 0:
        break
      time.sleep(0.1)

    if sm[msg_name].frameId == 0:
      return

    # Conectar VisionIPC
    try:
      vipc_client.connect(True)
    except Exception:
      return


    # Loop de captura
    while not self.stop_event.is_set():
      current_time = time.time()

      # Verificar intervalo
      if current_time - self.last_sent < self.interval_seconds:
        time.sleep(0.1)
        continue

      try:
        # Recibir frame (timeout 1 segundo)
        buf = vipc_client.recv(timeout_ms=1000)
        if buf is None:
          continue

        # Extraer imagen RGB
        rgb = self.extract_image(buf)
        if rgb is None:
          continue

        # Convertir a JPEG
        jpeg_data = self.rgb_to_jpeg(rgb)
        if jpeg_data is None:
          continue

        # Enviar por MQTT
        timestamp_ms = int(time.time() * 1000)
        self.send_image(jpeg_data, buf.frame_id, timestamp_ms)

        self.last_sent = current_time

      except Exception:
        self.error_count += 1
        time.sleep(0.5)

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

