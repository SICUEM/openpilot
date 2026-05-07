#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Esquive de obstáculos para el modo 3 (COMMA+JETSON).

A diferencia de adripilot_steering_pulse.py (cruceta MQTT, valores fijos,
dos fases), este módulo:
  - lee el último mensaje de la Jetson desde Params (productor: zmq_client en
    otro proceso, no globals)
  - escala intensity [-1,+1] a offsets de ángulo y curvatura
  - cancela por volante presionado, freno, watchdog, lat inactivo o sustitución
  - una sola fase (sin retorno: el LatControlTorque del Comma recentra)

Convención de signo: negativo = derecha, positivo = izquierda
(coherente con controlsd.py:894-897).
"""
from __future__ import annotations
from typing import Tuple


# Defaults (sembrados al param la primera vez que se lee y devuelve None)
DEFAULT_MAX_DURATION_MS = 2500.0   # ms — tope superior de duration_ms
DEFAULT_WATCHDOG_MS     = 400.0    # ms — sin heartbeat durante esquive → cancelar
DEFAULT_MAX_ANGLE       = 25.0     # grados — para |intensity|=1.0
DEFAULT_MAX_CURV        = 0.030    # 1/m  — para |intensity|=1.0


class ObstaclePulseState:
    """Estado del esquive activo. Una instancia por proceso controlsd."""

    def __init__(self) -> None:
        self.active: bool = False
        self.start_ts: float = 0.0
        self.duration_s: float = 0.0
        self.intensity: float = 0.0          # ya clampeado a [-1, +1]
        self.last_payload_ts: float = 0.0    # ts (wall-clock) del último mensaje recibido

    def ingest_new_message(self, payload: dict, now: float,
                           max_duration_ms: float = DEFAULT_MAX_DURATION_MS) -> None:
        """Carga un mensaje recibido de la Jetson (sustituye el actual)."""
        obstacle = bool(payload.get("obstacle", False))
        intensity = float(payload.get("intensity", 0.0))
        duration_ms = float(payload.get("duration_ms", 0.0))

        # Clamp intensity
        if intensity < -1.0:
            intensity = -1.0
        elif intensity > 1.0:
            intensity = 1.0

        # Cap duration
        if duration_ms < 0.0:
            duration_ms = 0.0
        if duration_ms > max_duration_ms:
            duration_ms = max_duration_ms

        # obstacle=False, intensity=0 o duration_ms=0 → cancelación / no-op
        if not obstacle or duration_ms == 0.0 or intensity == 0.0:
            self.active = False
            self.intensity = 0.0
            self.duration_s = 0.0
            self.last_payload_ts = now
            return

        self.active = True
        self.intensity = intensity
        self.duration_s = duration_ms / 1000.0
        self.start_ts = now
        self.last_payload_ts = now

    def get_offsets(self, now: float, carstate, lat_active: bool,
                    watchdog_ms: float = DEFAULT_WATCHDOG_MS,
                    max_angle: float = DEFAULT_MAX_ANGLE,
                    max_curv: float = DEFAULT_MAX_CURV) -> Tuple[float, float, str]:
        """Devuelve (angle_off_deg, curv_off, status) para este frame.

        status ∈ {"", "DODGING_LEFT", "DODGING_RIGHT",
                  "CANCELED_DRIVER", "CANCELED_STALE"}
        """
        if not self.active:
            return 0.0, 0.0, ""

        # Cancellation priority order (highest to lowest):
        #   1. lat_inactive — sistema sin control lateral, sin status visible
        #   2. driver override (steering/brake) → CANCELED_DRIVER
        #   3. natural expiry (duración cumplida) → "" (chequeado ANTES del
        #      watchdog: si la Jetson manda un único mensaje y la duración
        #      expira sin más mensajes, NO queremos marcar STALE)
        #   4. watchdog (sin heartbeat aún dentro de la duración) → CANCELED_STALE

        # Cancelación: lat inactivo (no es del conductor, status vacío)
        if not lat_active:
            self._reset()
            return 0.0, 0.0, ""

        # Cancelación: conductor (volante o freno)
        if carstate.steeringPressed or carstate.brakePressed:
            self._reset()
            return 0.0, 0.0, "CANCELED_DRIVER"

        # Fin natural por duración (comprobado antes del watchdog para no
        # solapar el status: si ya expiró naturalmente, no es "stale")
        elapsed = now - self.start_ts
        if elapsed >= self.duration_s:
            self._reset()
            return 0.0, 0.0, ""

        # Cancelación: watchdog (Jetson stale) — sólo si todavía dentro de la duración
        if (now - self.last_payload_ts) * 1000.0 > watchdog_ms:
            self._reset()
            return 0.0, 0.0, "CANCELED_STALE"

        # Aplicar offset proporcional a intensity
        angle_off = self.intensity * max_angle
        curv_off  = self.intensity * max_curv
        # Convención: negativo = derecha, positivo = izquierda
        status = "DODGING_RIGHT" if self.intensity < 0.0 else "DODGING_LEFT"
        return angle_off, curv_off, status

    def _reset(self) -> None:
        self.active = False
        self.intensity = 0.0
        self.duration_s = 0.0
