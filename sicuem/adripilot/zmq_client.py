#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cliente ZeroMQ para comunicación Comma <-> Jetson.

- Publica imágenes hacia la Jetson (PUB, fire-and-forget, nunca bloquea).
- Recibe torque desde la Jetson en un hilo daemon y lo guarda en Params.

Basado en el código proporcionado por el equipo de la Jetson.
"""
import json
import math
import struct
import threading
import time

import zmq

from openpilot.common.params import Params, UnknownKeyName
from openpilot.common.swaglog import cloudlog


def _parse_torque(data: bytes):
  """Convierte el payload de la Jetson en un float, sea cual sea su formato.

  Si elegimos un formato fijo y la Jetson manda otro (big-endian, double,
  texto…), el resultado tipico es un valor denormal (~1e-44) que en la UI
  sale como "0.00" — el sintoma de "imprime 0 aunque mande 0.5".

  Probamos las representaciones razonables y nos quedamos con la primera
  que caiga en el rango fisicamente posible para nuestro torque normalizado
  [-1, 1] (con holgura). Los denormals quedan filtrados por |v| < 1e-30.
  Devuelve None si nada cuadra.
  """
  candidates: list[float] = []
  n = len(data)
  if n == 4:
    candidates.append(struct.unpack("<f", data)[0])
    candidates.append(struct.unpack(">f", data)[0])
  elif n == 8:
    candidates.append(struct.unpack("<d", data)[0])
    candidates.append(struct.unpack(">d", data)[0])
  else:
    try:
      return float(data.decode().strip())
    except Exception:
      return None

  for v in candidates:
    if not math.isfinite(v):
      continue
    if v == 0.0 or 1e-30 < abs(v) < 100.0:
      return v
  return None


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
    # LINGER=0: al hacer close() no esperamos a drenar colas pendientes.
    # Critico para reload_jetson_config (cambio de IP en caliente): sin esto
    # context.term() podia bloquear y dejar el puerto 5555 en un estado raro.
    self._img_socket.setsockopt(zmq.LINGER, 0)
    self._img_socket.bind(f"tcp://*:{img_port}")

    # PULL: recepción de torque desde Jetson
    self._torque_socket = self._context.socket(zmq.PULL)
    self._torque_socket.setsockopt(zmq.LINGER, 0)
    # Timeout en recv para que el hilo listener no quede bloqueado para
    # siempre si la Jetson no envia nada; asi stop()+join() pueden cerrar
    # en tiempo finito incluso si la Jetson esta muerta.
    self._torque_socket.setsockopt(zmq.RCVTIMEO, 500)  # ms
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
    """Cierra los sockets y el contexto ZMQ limpiamente.

    Critico para cambiar IP en caliente: esta funcion se llama desde
    reload_jetson_config cada vez que el usuario modifica la config. Tiene
    que dejar el puerto 5555 LIBRE para que el siguiente bind funcione.
    """
    self._running = False
    # Esperar a que el hilo listener salga del recv (timeout RCVTIMEO=500ms)
    # y termine limpio antes de cerrar sockets/contexto. Sin join podiamos
    # tener el hilo vivo usando _torque_socket mientras otro thread lo cierra.
    if self._listener_thread.is_alive():
      self._listener_thread.join(timeout=1.5)
    try:
      self._img_socket.close(linger=0)
    except Exception:
      pass
    try:
      self._torque_socket.close(linger=0)
    except Exception:
      pass
    try:
      self._context.term()
    except Exception:
      pass
    cloudlog.info("ZMQClient: detenido")

  def _handle_obstacle_json(self, data: bytes) -> None:
    """Parsea un mensaje JSON del modo 3 (COMMA+JETSON) y lo publica en Params.

    Modelo "estado continuo" (v3): el formato esperado es
      {"obstacle": bool, "intensity": float [-1,+1]}
    El Comma se queda con el último mensaje recibido indefinidamente:
    obstacle=true → esquive activo con esa intensity hasta que llegue
    otro mensaje, obstacle=false → idle.
    Ya no existe `duration_ms` ni watchdog: si la Jetson se calla, el
    último estado se mantiene. Las únicas cancelaciones automáticas son
    volante / freno (CANCELED_DRIVER) y latActive=false.

    Si el JSON está mal formado o le faltan campos clave, se loguea y se
    descarta. NO se escribe en JetsonObstaclePulse para que el lado de
    controlsd no detecte un mensaje nuevo erróneo.
    """
    try:
      payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as e:
      cloudlog.error(f"ZMQClient: JSON obstáculo no decodificable: {e} bytes={data[:50]!r}")
      return

    if not isinstance(payload, dict):
      cloudlog.error(f"ZMQClient: JSON obstáculo no es objeto: {payload!r}")
      return

    intensity = payload.get("intensity")
    if not isinstance(intensity, (int, float)) or not math.isfinite(intensity):
      cloudlog.error(f"ZMQClient: JSON obstáculo intensity no válido (esperado float finito): {payload!r}")
      return

    now = time.time()
    cloudlog.info(f"ZMQClient: pulso obstáculo {payload}")
    # Orden: payload primero (json.dumps re-serializa para limpiar espacios y
    # tipos raros), timestamp después → si controlsd lee entremedias, ve un
    # ts viejo y procesa en el siguiente frame (no falsea sustitución).
    # put_nonblocking: el writer es un hilo aparte con cola FIFO, así no
    # bloqueamos el listener en disco. La FIFO preserva el orden pulse→ts.
    try:
      self._params.put("JetsonObstaclePulse", json.dumps(payload))
    except UnknownKeyName:
      cloudlog.error("JetsonObstaclePulse no registrado. Recompila common/params.cc.")
      return
    try:
      self._params.put("JetsonObstacleTimestamp", f"{now:.6f}")
    except UnknownKeyName:
      cloudlog.error("JetsonObstacleTimestamp no registrado. Recompila common/params.cc.")

  def _torque_listener(self):
    """Hilo daemon: espera torques/obstáculos de la Jetson y los guarda en Params.

    Drain pattern (estado-continuo):
      Cada `recv()` bloqueante despierta el hilo; acto seguido drenamos la
      cola ZMQ en modo no-bloqueante y nos quedamos SOLO con el ÚLTIMO
      mensaje de cada tipo (torque vs obstáculo). Ambos canales son
      estado-continuo (controlsd lee el último valor del param), así que
      procesar mensajes intermedios solo gasta CPU/I-O.

      Sin esto: si la Jetson manda `obstacle:true` a 30 Hz y luego un
      `obstacle:false`, el `false` quedaba al final de la cola y tardaba
      varios segundos en aplicarse (= "tarda en volver al modelo Comma").

    Guarda tambien un timestamp (wall-clock) por cada torque recibido. Eso
    permite a controlsd detectar que la Jetson se ha caido (watchdog): si el
    timestamp tiene mas de N ms de antiguedad, controlsd fuerza torque=0
    para que el volante no se quede atascado con un valor viejo.
    """
    while self._running:
      try:
        data = self._torque_socket.recv()
      except zmq.Again:
        # RCVTIMEO cumplido sin datos. Volvemos a comprobar _running y
        # seguimos esperando. Es el mecanismo que permite a stop() romper
        # el bucle en tiempo finito.
        continue
      except zmq.ZMQError as e:
        if e.errno == zmq.ETERM:
          break
        cloudlog.warning(f"ZMQClient: error recibiendo torque: {e}")
        continue
      except Exception as e:
        cloudlog.error(f"ZMQClient: error inesperado: {e}")
        continue

      # Drenar la cola: solo el ÚLTIMO mensaje de cada tipo nos importa.
      # Distinguimos por longitud (heredado del protocolo): len==4 → torque
      # clásico (float empaquetado, modo 1); len>4 → JSON modo 3.
      latest_torque: bytes | None = None
      latest_obstacle: bytes | None = None
      if len(data) > 4:
        latest_obstacle = data
      else:
        latest_torque = data
      # Bound defensivo para evitar bucle largo si llegan mensajes
      # continuamente más rápido de lo que drenamos (no debería pasar, pero
      # nunca dejes una recv-loop sin techo).
      drained_extra = 0
      while drained_extra < 1024:
        try:
          d = self._torque_socket.recv(zmq.NOBLOCK)
        except zmq.Again:
          break
        except zmq.ZMQError as e:
          if e.errno == zmq.ETERM:
            return
          cloudlog.warning(f"ZMQClient: error drenando cola: {e}")
          break
        drained_extra += 1
        if len(d) > 4:
          latest_obstacle = d
        else:
          latest_torque = d
      if drained_extra > 0:
        cloudlog.info(f"ZMQClient: drenados {drained_extra} mensajes (backlog), procesando solo el último de cada tipo")

      # Procesar obstáculo (si lo hay): el handler ya hace put_nonblocking.
      if latest_obstacle is not None:
        self._handle_obstacle_json(latest_obstacle)

      # Procesar torque clásico (si lo hay).
      if latest_torque is not None:
        torque = _parse_torque(latest_torque)
        if torque is None:
          # Payload irreconocible -> ignorar este mensaje (no escribimos
          # nada en params, asi el watchdog de controlsd lo marcara stale
          # y el volante quedara en 0 hasta que llegue un valor valido).
          cloudlog.error(f"ZMQClient: payload de torque irreconocible bytes={latest_torque.hex()} len={len(latest_torque)}")
          continue
        # Log de cada torque "efectivo" (post-drain) para verificacion del
        # formato y del valor que se publica al param.
        cloudlog.info(f"ZMQClient: torque recibido bytes={latest_torque.hex()} len={len(latest_torque)} -> {torque}")
        now = time.time()
        # Orden importante: primero el timestamp (marca que hay senal viva),
        # luego el valor. Si controlsd lee entre las dos escrituras, lee un
        # ts nuevo pero torque viejo -> aplica el valor anterior (seguro).
        # Si JetsonTorqueTimestamp no esta registrado en params.cc (no se
        # recompilo), seguimos publicando JetsonTorque para no romper la
        # UI, pero el watchdog en controlsd no podra validar frescura y
        # marcara stale -> torque=0 (fail-safe).
        try:
          self._params.put("JetsonTorqueTimestamp", f"{now:.6f}")
        except UnknownKeyName:
          if not getattr(self, "_warned_ts_param", False):
            cloudlog.error("JetsonTorqueTimestamp no registrado. Recompila common/params.cc para habilitar el watchdog del modo Jetson.")
            self._warned_ts_param = True
        self._params.put("JetsonTorque", str(torque))
