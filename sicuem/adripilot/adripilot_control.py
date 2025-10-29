#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Control AdriPilot - Manejo de comandos de control básico
"""
import time
from openpilot.common.params import Params

class AdriPilotControl:
  """Clase para manejar los comandos de control de AdriPilot."""

  def __init__(self):
    self.params = Params()
    self.last_command_time = 0
    self.command_duration = 0.5  # Duración del comando en segundos
    self.steering_angle = 0.0
    self.steering_speed = 2.0  # Grados por segundo

  def process_commands(self, car_control, car_state, sm):
    """Procesa todos los comandos de AdriPilot."""
    current_time = time.time()

    # Crear un controlsState dummy simple
    class DummyControlsState:
      def __init__(self):
        self.active = True
        self.vCruise = 40.0

    controls_state = DummyControlsState()

    # Procesar comandos de control básico
    self.process_control_commands(car_control, car_state, controls_state, current_time)

    # Procesar comandos de velocidad
    self.process_speed_commands(car_control, car_state, controls_state, current_time)

    # Limpiar comandos expirados
    self.clear_expired_commands(current_time)

  def process_control_commands(self, car_control, car_state, controls_state, current_time):
    """Procesa comandos de control básico (forward, break, tright, tleft)."""

    # Comando Forward (Aceleración)
    if self.params.get_bool("adripilot_forward"):
      self.handle_forward_command(car_control, car_state, controls_state)
      self.last_command_time = current_time

    # Comando Break (Frenado)
    if self.params.get_bool("adripilot_break"):
      self.handle_break_command(car_control, car_state, controls_state)
      self.last_command_time = current_time

    # Comando Tright (Giro a la derecha)
    if self.params.get_bool("adripilot_tright"):
      self.handle_tright_command(car_control, car_state, controls_state)
      self.last_command_time = current_time

    # Comando Tleft (Giro a la izquierda)
    if self.params.get_bool("adripilot_tleft"):
      self.handle_tleft_command(car_control, car_state, controls_state)
      self.last_command_time = current_time

  def process_speed_commands(self, car_control, car_state, controls_state, current_time):
    """Procesa comandos de velocidad (increase/decrease)."""

    # Aumentar velocidad
    if self.params.get_bool("adripilot_speed_increase"):
      self.handle_speed_increase_command(car_control, car_state, controls_state)
      self.last_command_time = current_time

    # Reducir velocidad
    if self.params.get_bool("adripilot_speed_decrease"):
      self.handle_speed_decrease_command(car_control, car_state, controls_state)
      self.last_command_time = current_time

  def handle_forward_command(self, car_control, car_state, controls_state):
    """Maneja el comando de aceleración/avance."""
    if not controls_state.active:
      print("⚠️ Comando FORWARD ignorado: controles no activos")
      return

    # Aumentar ligeramente la aceleración
    if hasattr(car_control, 'actuators'):
      car_control.actuators.accel = min(car_control.actuators.accel + 0.1, 1.0)
      print("🚀 Comando FORWARD ejecutado: aceleración aumentada")

    # Limpiar comando
    self.params.put_bool("adripilot_forward", False)

  def handle_break_command(self, car_control, car_state, controls_state):
    """Maneja el comando de frenado."""
    if not controls_state.active:
      print("⚠️ Comando BREAK ignorado: controles no activos")
      return

    # Aplicar frenado suave
    if hasattr(car_control, 'actuators'):
      car_control.actuators.brake = min(car_control.actuators.brake + 0.2, 1.0)
      car_control.actuators.accel = max(car_control.actuators.accel - 0.2, -1.0)
      print("🛑 Comando BREAK ejecutado: frenado aplicado")

    # Limpiar comando
    self.params.put_bool("adripilot_break", False)

  def handle_tright_command(self, car_control, car_state, controls_state):
    """Maneja el comando de giro a la derecha."""
    if not controls_state.active:
      print("⚠️ Comando TRIGHT ignorado: controles no activos")
      return

    # Aplicar giro suave a la derecha
    if hasattr(car_control, 'actuators'):
      self.steering_angle = min(self.steering_angle + self.steering_speed, 30.0)
      car_control.actuators.steer = self.steering_angle / 30.0  # Normalizar a -1,1
      print(f"↗️ Comando TRIGHT ejecutado: ángulo {self.steering_angle:.1f}°")

    # Limpiar comando
    self.params.put_bool("adripilot_tright", False)

  def handle_tleft_command(self, car_control, car_state, controls_state):
    """Maneja el comando de giro a la izquierda."""
    if not controls_state.active:
      print("⚠️ Comando TLEFT ignorado: controles no activos")
      return

    # Aplicar giro suave a la izquierda
    if hasattr(car_control, 'actuators'):
      self.steering_angle = max(self.steering_angle - self.steering_speed, -30.0)
      car_control.actuators.steer = self.steering_angle / 30.0  # Normalizar a -1,1
      print(f"↖️ Comando TLEFT ejecutado: ángulo {self.steering_angle:.1f}°")

    # Limpiar comando
    self.params.put_bool("adripilot_tleft", False)

  def handle_speed_increase_command(self, car_control, car_state, controls_state):
    """Maneja el comando de aumentar velocidad."""
    if not controls_state.active:
      print("⚠️ Comando SPEED INCREASE ignorado: controles no activos")
      return

    # Obtener velocidad actual desde setSpeed (m/s) y convertir a km/h
    current_set_speed_ms = car_control.hudControl.setSpeed
    current_v_cruise_kmh = current_set_speed_ms * 3.6

    # Aumentar velocidad de crucero en 1 km/h
    new_v_cruise_kmh = min(current_v_cruise_kmh + 1.0, 145.0)  # Máximo 145 km/h
    new_set_speed_ms = new_v_cruise_kmh / 3.6  # Convertir a m/s

    # Modificar directamente el hudControl
    car_control.hudControl.setSpeed = new_set_speed_ms
    car_control.vCruise = new_v_cruise_kmh

    # También usar el sistema de parámetros como respaldo
    self.params.put_int_nonblocking("adripilot_speed_target", int(new_v_cruise_kmh))
    self.params.put_bool("adripilot_speed_increase", False)  # Limpiar comando

    print(f"⬆️ Comando SPEED INCREASE ejecutado: {current_v_cruise_kmh:.1f} → {new_v_cruise_kmh:.1f} km/h")

  def handle_speed_decrease_command(self, car_control, car_state, controls_state):
    """Maneja el comando de reducir velocidad."""
    if not controls_state.active:
      print("⚠️ Comando SPEED DECREASE ignorado: controles no activos")
      return

    # Obtener velocidad actual desde setSpeed (m/s) y convertir a km/h
    current_set_speed_ms = car_control.hudControl.setSpeed
    current_v_cruise_kmh = current_set_speed_ms * 3.6

    # Reducir velocidad de crucero en 1 km/h
    new_v_cruise_kmh = max(current_v_cruise_kmh - 1.0, 8.0)  # Mínimo 8 km/h
    new_set_speed_ms = new_v_cruise_kmh / 3.6  # Convertir a m/s

    # Modificar directamente el hudControl
    car_control.hudControl.setSpeed = new_set_speed_ms
    car_control.vCruise = new_v_cruise_kmh

    # También usar el sistema de parámetros como respaldo
    self.params.put_int_nonblocking("adripilot_speed_target", int(new_v_cruise_kmh))
    self.params.put_bool("adripilot_speed_decrease", False)  # Limpiar comando

    print(f"⬇️ Comando SPEED DECREASE ejecutado: {current_v_cruise_kmh:.1f} → {new_v_cruise_kmh:.1f} km/h")

  def clear_expired_commands(self, current_time):
    """Limpia comandos que han expirado."""
    if current_time - self.last_command_time > self.command_duration:
      # Resetear ángulo de dirección gradualmente
      if abs(self.steering_angle) > 0.1:
        self.steering_angle *= 0.9  # Reducir gradualmente
      else:
        self.steering_angle = 0.0

# Instancia global del controlador
adripilot_control = AdriPilotControl()
