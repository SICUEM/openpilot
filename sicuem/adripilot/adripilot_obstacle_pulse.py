#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Esquive de obstáculos para el modo 3 (COMMA+JETSON).

Modelo "estado continuo" (v3, 2026-05-12):
  - La Jetson envía un JSON {"obstacle": bool, "intensity": float} cuando
    quiere cambiar de estado.
  - El Comma se queda con el ÚLTIMO mensaje recibido y actúa según él:
      · obstacle=true  + intensity≠0 → aplica offset proporcional al volante
      · obstacle=false (o intensity=0) → no esquiva, manda el modelo del Comma
  - YA NO existe `duration_ms`.
  - YA NO existe watchdog: el último valor se mantiene hasta que llegue
    otro. Si la Jetson manda `true` y luego se queda callada, el esquive
    sigue activo hasta que la propia Jetson mande `false`, o el conductor
    intervenga (volante/freno), o el control lateral del openpilot se
    desactive (latActive=false).

A diferencia de adripilot_steering_pulse.py (cruceta MQTT, valores fijos,
dos fases), este módulo:
  - lee el último mensaje de la Jetson desde Params (productor: zmq_client en
    otro proceso, no globals)
  - escala intensity [-1,+1] a offsets de ángulo y curvatura
  - cancela por volante presionado, freno, lat inactivo o por recibir un
    mensaje con obstacle=false / intensity=0

Convención de signo: negativo = derecha, positivo = izquierda
(coherente con controlsd.py:894-897).
"""
from __future__ import annotations
from typing import Tuple


# Defaults (sembrados al param la primera vez que se lee y devuelve None)
DEFAULT_MAX_ANGLE       = 25.0     # grados — para |intensity|=1.0
DEFAULT_MAX_CURV        = 0.030    # 1/m  — para |intensity|=1.0


class ObstaclePulseState:
    """Estado del esquive activo. Una instancia por proceso controlsd."""

    def __init__(self) -> None:
        self.active: bool = False
        self.intensity: float = 0.0          # ya clampeado a [-1, +1]
        self.last_payload_ts: float = 0.0    # ts (wall-clock) del último mensaje; informativo

    def ingest_new_message(self, payload: dict, now: float) -> None:
        """Carga un mensaje recibido de la Jetson (sustituye el actual).

        Modelo "estado continuo": el mensaje describe la situación actual,
        no un pulso con duración. obstacle=true + intensity≠0 → esquivar;
        obstacle=false o intensity=0 → no esquivar (manda el modelo del Comma).
        """
        obstacle = bool(payload.get("obstacle", False))
        intensity = float(payload.get("intensity", 0.0))

        # Clamp intensity
        if intensity < -1.0:
            intensity = -1.0
        elif intensity > 1.0:
            intensity = 1.0

        self.last_payload_ts = now

        # obstacle=False o intensity=0 → no aplicar esquive (estado idle)
        if not obstacle or intensity == 0.0:
            self.active = False
            self.intensity = 0.0
            return

        self.active = True
        self.intensity = intensity

    def get_offsets(self, now: float, carstate, lat_active: bool,
                    max_angle: float = DEFAULT_MAX_ANGLE,
                    max_curv: float = DEFAULT_MAX_CURV) -> Tuple[float, float, str]:
        """Devuelve (angle_off_deg, curv_off, status) para este frame.

        status ∈ {"", "DODGING_LEFT", "DODGING_RIGHT", "CANCELED_DRIVER"}
        """
        if not self.active:
            return 0.0, 0.0, ""

        # Cancellation priority order (highest to lowest):
        #   1. lat_inactive — sistema sin control lateral, sin status visible
        #   2. driver override (steering/brake) → CANCELED_DRIVER
        # Sin watchdog: mientras no llegue obstacle=false ni se desactive
        # lateral ni intervenga el conductor, el esquive se mantiene con
        # el último valor recibido.

        # Cancelación: lat inactivo (no es del conductor, status vacío)
        if not lat_active:
            self._reset()
            return 0.0, 0.0, ""

        # Cancelación: conductor (volante o freno)
        if carstate.steeringPressed or carstate.brakePressed:
            self._reset()
            return 0.0, 0.0, "CANCELED_DRIVER"

        # Aplicar offset proporcional a intensity
        angle_off = self.intensity * max_angle
        curv_off  = self.intensity * max_curv
        # Convención: negativo = derecha, positivo = izquierda
        status = "DODGING_RIGHT" if self.intensity < 0.0 else "DODGING_LEFT"
        return angle_off, curv_off, status

    def _reset(self) -> None:
        self.active = False
        self.intensity = 0.0
