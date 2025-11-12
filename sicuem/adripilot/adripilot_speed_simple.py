#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Control de Velocidad AdriPilot - Enfoque Simplificado
Sin dependencia de controlsState
"""
import time
from openpilot.common.params import Params

class AdriPilotSpeedSimple:
  """Controlador de velocidad simplificado para AdriPilot."""

  def __init__(self):
    self.params = Params()
    self.speed_increment = 1.0  # km/h

  def process_speed_commands(self, car_control, car_state):
    """Procesa comandos de velocidad de forma directa."""

    # Verificar comandos de velocidad
    speed_increase = self.params.get_bool("adripilot_speed_increase")
    speed_decrease = self.params.get_bool("adripilot_speed_decrease")

    if speed_increase or speed_decrease:
      # Obtener velocidad actual desde setSpeed
      current_speed = self.get_current_speed(car_control)

      # Calcular nueva velocidad
      if speed_increase:
        new_speed = min(current_speed + self.speed_increment, 145.0)
        command_type = "INCREASE"
      else:
        new_speed = max(current_speed - self.speed_increment, 8.0)
        command_type = "DECREASE"

      # Aplicar cambios directamente
      self.apply_speed_changes(car_control, new_speed)

      # Limpiar comandos
      self.params.put_bool("adripilot_speed_increase", False)
      self.params.put_bool("adripilot_speed_decrease", False)

      print(f"🎯 Comando SPEED {command_type} ejecutado: {current_speed:.1f} → {new_speed:.1f} km/h")

  def get_current_speed(self, car_control):
    """Obtiene la velocidad actual desde setSpeed."""
    # Obtener desde hudControl.setSpeed (m/s) y convertir a km/h
    if hasattr(car_control, 'hudControl') and hasattr(car_control.hudControl, 'setSpeed'):
      set_speed_ms = car_control.hudControl.setSpeed
      if set_speed_ms > 0:
        return set_speed_ms * 3.6  # Convertir a km/h

    # Fallback: 40 km/h
    return 40.0

  def apply_speed_changes(self, car_control, new_speed_kmh):
    """Aplica cambios de velocidad directamente."""
    new_speed_ms = new_speed_kmh / 3.6  # Convertir a m/s

    # 1. Modificar hudControl.setSpeed
    if hasattr(car_control, 'hudControl'):
      car_control.hudControl.setSpeed = new_speed_ms
      print(f"   📊 hudControl.setSpeed: {new_speed_ms:.2f} m/s")

    # 2. Modificar vCruise
    if hasattr(car_control, 'vCruise'):
      car_control.vCruise = new_speed_kmh
      print(f"   📊 vCruise: {new_speed_kmh:.1f} km/h")

    # 3. Usar parámetros como respaldo
    self.params.put("adripilot_speed_target", str(int(new_speed_kmh)))
    print(f"   📊 Params: adripilot_speed_target = {int(new_speed_kmh)}")

# Instancia global del controlador de velocidad simplificado
adripilot_speed_simple = AdriPilotSpeedSimple()






