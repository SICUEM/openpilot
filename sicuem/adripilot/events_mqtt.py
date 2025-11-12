#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from datetime import datetime
import os
from typing import Optional

import paho.mqtt.publish as publish

from openpilot.common.params import Params


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


def send_event(title: str,
               message: str,
               priority: int,
               dongle_id: Optional[str] = None,
               event_name: Optional[str] = None,
               event_type: Optional[str] = None) -> None:
  broker, port = _load_broker()
  did = dongle_id or _get_dongle_id()
  topic = f"telemetry_mqtt/{did}/event"
  payload = {
    "dongle_id": did,
    "title": title,
    "message": message,
    "priority": int(priority),
    "timestamp": datetime.utcnow().isoformat() + "Z",
  }
  if event_name is not None:
    payload["event_name"] = event_name
  if event_type is not None:
    payload["event_type"] = event_type
  try:
    publish.single(topic, json.dumps(payload), hostname=broker, port=port, qos=0)
    # Log solo en desarrollo, comentar en producción si es necesario
    print(f"📤 Evento MQTT enviado a {topic}: {payload.get('title', 'N/A')} - {payload.get('message', 'N/A')}")
  except Exception as e:
    # Log del error para diagnóstico
    print(f"❌ Error al enviar evento MQTT a {broker}:{port}: {e}")
    raise  # Re-lanzar para que se capture en controlsd.py


def send_alert(alert) -> None:
  """Send an Events.Alert-like object.

  Expects attributes: alert_text_1, alert_text_2, priority, alert_type
  """
  try:
    title = getattr(alert, "alert_text_1", "") or ""
    msg = getattr(alert, "alert_text_2", "") or ""
    prio = getattr(alert, "priority", 0) or 0
    atype = getattr(alert, "alert_type", "") or ""

    # Validar que tenemos datos mínimos
    if not title and not msg:
      print(f"⚠️ AdriPilot: Alerta sin título ni mensaje, alert_type={atype}")
      return

    ev_name = None
    ev_type = None
    if "/" in atype:
      parts = atype.split("/", 1)
      if len(parts) == 2:
        ev_name, ev_type = parts[0], parts[1]

    send_event(title, msg, int(prio), event_name=ev_name, event_type=ev_type)
  except Exception as e:
    print(f"❌ AdriPilot: Error en send_alert: {e}")
    raise  # Re-lanzar para diagnóstico


