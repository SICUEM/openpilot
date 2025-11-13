#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Giro Temporal del Volante AdriPilot
Usa variables globales para comunicación entre mqtt_comandos y controlsd
"""
import time

# Variables globales para comandos de giro temporal
adripilot_steering_pulse_start = None  # Timestamp del inicio del pulso
adripilot_steering_pulse_direction = None  # "left" o "right"
adripilot_steering_pulse_duration = 0.8  # Duración del pulso en segundos
adripilot_steering_pulse_angle = 3.0  # Grados de giro

def set_steering_pulse(direction):
  """Activa un pulso de giro temporal del volante."""
  global adripilot_steering_pulse_start, adripilot_steering_pulse_direction
  adripilot_steering_pulse_start = time.time()
  adripilot_steering_pulse_direction = direction
  print(f"🔄 AdriPilot: Pulso de giro temporal activado - dirección: {direction}, timestamp: {adripilot_steering_pulse_start}")

  # Verificar que se guardó correctamente
  print(f"🔄 AdriPilot: Verificación - start: {adripilot_steering_pulse_start}, direction: {adripilot_steering_pulse_direction}")

def get_steering_pulse():
  """Obtiene el estado actual del pulso de giro."""
  global adripilot_steering_pulse_start, adripilot_steering_pulse_direction, adripilot_steering_pulse_duration

  # Debug: verificar estado de las variables globales
  # print(f"🔍 get_steering_pulse: start={adripilot_steering_pulse_start}, direction={adripilot_steering_pulse_direction}")

  if adripilot_steering_pulse_start is None or adripilot_steering_pulse_direction is None:
    return None, None, False

  current_time = time.time()
  elapsed = current_time - adripilot_steering_pulse_start

  # Si el pulso ha terminado, limpiar
  if elapsed >= adripilot_steering_pulse_duration:
    print(f"⏰ AdriPilot: Pulso expirado - elapsed: {elapsed:.2f}s, duration: {adripilot_steering_pulse_duration}s")
    adripilot_steering_pulse_start = None
    adripilot_steering_pulse_direction = None
    return None, None, False

  return adripilot_steering_pulse_start, adripilot_steering_pulse_direction, True

def clear_steering_pulse():
  """Limpia el pulso de giro temporal."""
  global adripilot_steering_pulse_start, adripilot_steering_pulse_direction
  adripilot_steering_pulse_start = None
  adripilot_steering_pulse_direction = None

