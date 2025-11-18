#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Giro Temporal del Volante AdriPilot
Usa variables globales para comunicación entre mqtt_comandos y controlsd

Funcionamiento:
1. Fase inicial (0.5s): Gira el volante en la dirección indicada
2. Fase de retorno (0.5s): Gira el volante en la dirección contraria para volver al estado original
"""
import time

# Variables globales para comandos de giro temporal
adripilot_steering_pulse_start = None  # Timestamp del inicio del pulso
adripilot_steering_pulse_direction = None  # "left" o "right"
adripilot_steering_pulse_initial_duration = 0.5  # Duración de la fase inicial (giro) en segundos
adripilot_steering_pulse_return_duration = 0.5  # Duración de la fase de retorno en segundos
adripilot_steering_pulse_angle = 3.0  # Grados de giro

# Duración total = fase inicial + fase de retorno
adripilot_steering_pulse_duration = adripilot_steering_pulse_initial_duration + adripilot_steering_pulse_return_duration

def set_steering_pulse(direction):
  """Activa un pulso de giro temporal del volante con dos fases."""
  global adripilot_steering_pulse_start, adripilot_steering_pulse_direction
  adripilot_steering_pulse_start = time.time()
  adripilot_steering_pulse_direction = direction
  print(f"🔄 AdriPilot: Pulso de giro temporal activado - dirección: {direction}, timestamp: {adripilot_steering_pulse_start}")
  print(f"🔄 AdriPilot: Fase 1 (0.5s): Giro {direction} → Fase 2 (0.5s): Retorno")

  # Verificar que se guardó correctamente
  print(f"🔄 AdriPilot: Verificación - start: {adripilot_steering_pulse_start}, direction: {adripilot_steering_pulse_direction}")

def get_steering_pulse():
  """Obtiene el estado actual del pulso de giro.

  Returns:
    tuple: (pulse_start, direction, is_active, phase, effective_direction)
      - pulse_start: Timestamp del inicio del pulso
      - direction: Dirección original ("left" o "right")
      - is_active: True si el pulso está activo
      - phase: "initial" o "return" según la fase actual
      - effective_direction: Dirección efectiva a aplicar ("left", "right", o None)
  """
  global adripilot_steering_pulse_start, adripilot_steering_pulse_direction
  global adripilot_steering_pulse_initial_duration, adripilot_steering_pulse_return_duration

  if adripilot_steering_pulse_start is None or adripilot_steering_pulse_direction is None:
    return None, None, False, None, None

  current_time = time.time()
  elapsed = current_time - adripilot_steering_pulse_start

  # Si el pulso ha terminado completamente, limpiar
  if elapsed >= adripilot_steering_pulse_duration:
    print(f"⏰ AdriPilot: Pulso completado - elapsed: {elapsed:.2f}s, duration: {adripilot_steering_pulse_duration}s")
    adripilot_steering_pulse_start = None
    adripilot_steering_pulse_direction = None
    return None, None, False, None, None

  # Determinar la fase actual
  if elapsed < adripilot_steering_pulse_initial_duration:
    # Fase inicial: girar en la dirección indicada
    phase = "initial"
    effective_direction = adripilot_steering_pulse_direction
  else:
    # Fase de retorno: girar en la dirección contraria
    phase = "return"
    effective_direction = "right" if adripilot_steering_pulse_direction == "left" else "left"

  return adripilot_steering_pulse_start, adripilot_steering_pulse_direction, True, phase, effective_direction

def clear_steering_pulse():
  """Limpia el pulso de giro temporal."""
  global adripilot_steering_pulse_start, adripilot_steering_pulse_direction
  adripilot_steering_pulse_start = None
  adripilot_steering_pulse_direction = None

