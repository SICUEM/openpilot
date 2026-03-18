#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cliente ZeroMQ para comunicación Comma <-> Jetson.

- Publica imágenes hacia la Jetson (PUB, fire-and-forget, nunca bloquea).
- Recibe torque desde la Jetson en un hilo daemon y lo guarda en Params.

Basado en el código proporcionado por el equipo de la Jetson.
"""
import struct
import threading

import zmq

from openpilot.common.params import Params
from openpilot.common.swaglog import cloudlog


class ZMQClient:
  """Comunicación ZeroMQ entre Comma (pcA) y Jetson (pcB)."""

  def __init__(self, jetson_ip, img_port=5555, torque_port=5556, jpeg_quality=80):
    """
    Args:
      jetson_ip:    IP de la Jetson en la red local. Ej: "192.168.1.50"
      img_port:     Puerto para enviar imágenes (default 5555).
      torque_port:  Puerto para recibir torque (default 5556).
      jpeg_quality: Calidad JPEG 0-100 (default 80).
    """
    self._jpeg_quality = jpeg_quality
    self._params = Params()
    self._running = False

    self._context = zmq.Context()

    # PUB: envío de imágenes — fire-and-forget, nunca bloquea
    self._img_socket = self._context.socket(zmq.PUB)
    self._img_socket.setsockopt(zmq.SNDHWM, 1)  # descarta si Jetson va lento
    self._img_socket.bind(f"tcp://*:{img_port}")

    # PULL: recepción de torque desde Jetson
    self._torque_socket = self._context.socket(zmq.PULL)
    self._torque_socket.connect(f"tcp://{jetson_ip}:{torque_port}")

    self._listener_thread = threading.Thread(
      target=self._torque_listener,
      daemon=True,
      name="jetson-torque-listener",
    )

    cloudlog.info(f"ZMQClient: configurado para Jetson en {jetson_ip} (img:{img_port}, torque:{torque_port})")

  def start(self):
    """Arranca el hilo de escucha de torque. Llamar una vez antes del loop."""
    self._running = True
    self._listener_thread.start()
    cloudlog.info("ZMQClient: hilo de escucha de torque iniciado")

  def send_image(self, jpeg_data):
    """
    Envía datos JPEG ya codificados a la Jetson.
    No bloquea nunca: si la Jetson no está lista, el frame se descarta.

    Args:
      jpeg_data: bytes con la imagen JPEG ya codificada
    """
    try:
      self._img_socket.send(jpeg_data, zmq.NOBLOCK)
    except zmq.Again:
      pass  # Socket lleno, frame descartado (comportamiento esperado)
    except zmq.ZMQError as e:
      cloudlog.warning(f"ZMQClient: error enviando imagen: {e}")

  def stop(self):
    """Cierra los sockets y el contexto ZMQ limpiamente."""
    self._running = False
    self._img_socket.close()
    self._torque_socket.close()
    self._context.term()
    cloudlog.info("ZMQClient: detenido")

  def _torque_listener(self):
    """Hilo daemon: espera torques de la Jetson y los guarda en Params."""
    while self._running:
      try:
        data = self._torque_socket.recv()
        torque = struct.unpack("f", data)[0]
        self._params.put("JetsonTorque", str(torque))
      except zmq.ZMQError as e:
        if e.errno == zmq.ETERM:
          break
        cloudlog.warning(f"ZMQClient: error recibiendo torque: {e}")
      except Exception as e:
        cloudlog.error(f"ZMQClient: error inesperado: {e}")
