#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import time
from datetime import datetime
import os
from typing import Optional, Dict

import paho.mqtt.publish as publish

from openpilot.common.params import Params


# Cooldown en segundos antes de re-enviar el mismo evento
EVENT_COOLDOWN_SECONDS = 12  # 12 segundos (entre 10-15 como se discutió)

# Diccionario para trackear último envío de cada evento (basado en alert_type)
_event_last_sent: Dict[str, float] = {}  # alert_type -> timestamp último envío


def _load_broker() -> tuple[str, int]:
  base_path = os.path.dirname(os.path.abspath(__file__))
  cfg_path = os.path.join(base_path, "config_mqtt.json")
  try:
    with open(cfg_path, "r") as f:
      cfg = json.load(f)
    broker = cfg.get("broker", "localhost")
    port = int(cfg.get("broker_port", 1883))
    return broker, port
  except Exception:
    return "localhost", 1883


def _get_dongle_id() -> str:
  params = Params()
  raw = params.get("DongleId")
  return raw.decode("utf-8") if raw else "UnregisteredDevice"


def _should_send_event(alert_type: str) -> bool:
  """Verifica si se debe enviar un evento basado en el cooldown.

  Args:
    alert_type: Tipo de alerta (ej: "controlsLagging/warning")

  Returns:
    True si se debe enviar, False si está en cooldown
  """
  if not alert_type:
    return False

  current_time = time.time()
  last_sent = _event_last_sent.get(alert_type, 0)

  # Si nunca se ha enviado o ha pasado el cooldown, permitir envío
  if last_sent == 0 or (current_time - last_sent) >= EVENT_COOLDOWN_SECONDS:
    _event_last_sent[alert_type] = current_time
    return True

  return False


def send_event_full(title: str,
                    message: str,
                    priority: int,
                    dongle_id: Optional[str] = None,
                    event_name: Optional[str] = None,
                    event_type: Optional[str] = None,
                    alert_type: Optional[str] = None) -> None:
  """Envía un evento completo por MQTT con toda su información.

  Args:
    title: Título del evento
    message: Mensaje del evento
    priority: Prioridad del evento (0-5)
    dongle_id: ID del dispositivo (opcional)
    event_name: Nombre del evento (ej: "controlsLagging")
    event_type: Tipo del evento (ej: "warning")
    alert_type: Tipo completo de alerta (ej: "controlsLagging/warning")
  """
  broker, port = _load_broker()
  did = dongle_id or _get_dongle_id()
  topic = f"telemetry_mqtt/{did}/event"

  # Construir alert_type si no se proporciona
  if not alert_type:
    if event_name and event_type:
      alert_type = f"{event_name}/{event_type}"
    elif event_name:
      alert_type = event_name
    else:
      alert_type = "unknown/unknown"

  # Verificar cooldown antes de enviar
  if not _should_send_event(alert_type):
    # Evento en cooldown, no enviar
    return

  # Payload completo con toda la información del evento
  payload = {
    "dongle_id": did,
    "event_name": event_name or "",
    "event_type": event_type or "",
    "alert_type": alert_type,
    "title": title or "",
    "message": message or "",
    "priority": priority,
    "timestamp": datetime.utcnow().isoformat() + "Z",
  }

  try:
    publish.single(topic, json.dumps(payload), hostname=broker, port=port, qos=0)
    # Log reducido solo en desarrollo
    # print(f"📤 Evento completo enviado a {topic}: {alert_type}")
  except Exception as e:
    print(f"❌ Error al enviar evento completo a {broker}:{port}: {e}")
    # No re-lanzar para no afectar el loop de control


def send_alert(alert) -> None:
  """Send an Events.Alert-like object (envía evento completo con cooldown).

  Expects attributes: alert_text_1, alert_text_2, priority, alert_type, event_name, event_type
  """
  try:
    # Obtener información del alert
    alert_type = getattr(alert, "alert_type", "") or ""
    title = getattr(alert, "alert_text_1", "") or ""
    message = getattr(alert, "alert_text_2", "") or ""
    priority = getattr(alert, "priority", 0)

    # Extraer event_name y event_type desde alert_type si está en formato "eventName/eventType"
    event_name = None
    event_type = None
    if alert_type and "/" in alert_type:
      parts = alert_type.split("/", 1)
      event_name = parts[0] if len(parts) > 0 else None
      event_type = parts[1] if len(parts) > 1 else None
    elif alert_type:
      event_name = alert_type

    # Validar que tenemos alert_type
    if not alert_type:
      return

    # Enviar evento completo con cooldown
    send_event_full(
      title=title,
      message=message,
      priority=priority,
      event_name=event_name,
      event_type=event_type,
      alert_type=alert_type
    )

  except Exception as e:
    print(f"❌ AdriPilot: Error en send_alert: {e}")
    # No re-lanzar para no afectar el loop de control
