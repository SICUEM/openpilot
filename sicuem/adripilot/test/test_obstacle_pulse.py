"""Tests unitarios del esquive de obstáculos (modo 3 COMMA+JETSON).

Modelo "estado continuo" (v3, 2026-05-12):
  - El payload no lleva `duration_ms`.
  - NO hay watchdog: el Comma se queda con el último valor recibido
    indefinidamente hasta que la Jetson mande otro mensaje, o el conductor
    intervenga, o se desactive el control lateral.
"""
import unittest
from unittest.mock import MagicMock

from openpilot.sicuem.adripilot.adripilot_obstacle_pulse import (
    ObstaclePulseState,
    DEFAULT_MAX_ANGLE,
    DEFAULT_MAX_CURV,
)


def _carstate(steering_pressed=False, brake_pressed=False):
    cs = MagicMock()
    cs.steeringPressed = steering_pressed
    cs.brakePressed = brake_pressed
    return cs


class TestObstaclePulseState(unittest.TestCase):

    def test_idle_returns_zero_offsets(self):
        s = ObstaclePulseState()
        a, c, st = s.get_offsets(now=0.0, carstate=_carstate(), lat_active=True)
        self.assertEqual(a, 0.0)
        self.assertEqual(c, 0.0)
        self.assertEqual(st, "")

    def test_ingest_basic_left(self):
        s = ObstaclePulseState()
        s.ingest_new_message({"obstacle": True, "intensity": 0.4}, now=10.0)
        self.assertTrue(s.active)
        self.assertAlmostEqual(s.intensity, 0.4)

    def test_offsets_proportional_to_intensity(self):
        s = ObstaclePulseState()
        s.ingest_new_message({"obstacle": True, "intensity": -0.5}, now=10.0)
        a, c, st = s.get_offsets(now=10.3, carstate=_carstate(), lat_active=True)
        self.assertAlmostEqual(a, -0.5 * DEFAULT_MAX_ANGLE)
        self.assertAlmostEqual(c, -0.5 * DEFAULT_MAX_CURV)
        self.assertEqual(st, "DODGING_RIGHT")

    def test_offsets_left_status(self):
        s = ObstaclePulseState()
        s.ingest_new_message({"obstacle": True, "intensity": 0.7}, now=10.0)
        a, c, st = s.get_offsets(now=10.3, carstate=_carstate(), lat_active=True)
        self.assertGreater(a, 0)
        self.assertGreater(c, 0)
        self.assertEqual(st, "DODGING_LEFT")

    def test_last_value_persists_indefinitely(self):
        """Sin watchdog: si la Jetson manda obstacle=true y luego se queda
        callada durante mucho tiempo, el esquive sigue activo con la última
        intensity hasta que llegue otro mensaje o intervenga el conductor."""
        s = ObstaclePulseState()
        s.ingest_new_message({"obstacle": True, "intensity": -0.5}, now=10.0)
        # 60 segundos sin recibir nada → sigue esquivando igualmente
        a, c, st = s.get_offsets(now=70.0, carstate=_carstate(), lat_active=True)
        self.assertAlmostEqual(a, -0.5 * DEFAULT_MAX_ANGLE)
        self.assertAlmostEqual(c, -0.5 * DEFAULT_MAX_CURV)
        self.assertEqual(st, "DODGING_RIGHT")

    def test_cancel_steering_pressed(self):
        s = ObstaclePulseState()
        s.ingest_new_message({"obstacle": True, "intensity": -0.5}, now=10.0)
        a, c, st = s.get_offsets(now=10.3, carstate=_carstate(steering_pressed=True), lat_active=True)
        self.assertEqual((a, c), (0.0, 0.0))
        self.assertEqual(st, "CANCELED_DRIVER")
        self.assertFalse(s.active)

    def test_cancel_brake_pressed(self):
        s = ObstaclePulseState()
        s.ingest_new_message({"obstacle": True, "intensity": 0.5}, now=10.0)
        _, _, st = s.get_offsets(now=10.3, carstate=_carstate(brake_pressed=True), lat_active=True)
        self.assertEqual(st, "CANCELED_DRIVER")

    def test_cancel_lat_inactive(self):
        s = ObstaclePulseState()
        s.ingest_new_message({"obstacle": True, "intensity": -0.5}, now=10.0)
        a, c, st = s.get_offsets(now=10.3, carstate=_carstate(), lat_active=False)
        self.assertEqual((a, c, st), (0.0, 0.0, ""))
        self.assertFalse(s.active)

    def test_clamp_intensity(self):
        s = ObstaclePulseState()
        s.ingest_new_message({"obstacle": True, "intensity": 99.0}, now=0.0)
        self.assertEqual(s.intensity, 1.0)
        s.ingest_new_message({"obstacle": True, "intensity": -99.0}, now=0.0)
        self.assertEqual(s.intensity, -1.0)

    def test_obstacle_false_cancels(self):
        """Mensaje con obstacle=false → idle inmediato."""
        s = ObstaclePulseState()
        s.ingest_new_message({"obstacle": True, "intensity": -0.5}, now=10.0)
        self.assertTrue(s.active)
        s.ingest_new_message({"obstacle": False, "intensity": 0.0}, now=10.2)
        self.assertFalse(s.active)
        a, c, st = s.get_offsets(now=10.25, carstate=_carstate(), lat_active=True)
        self.assertEqual((a, c, st), (0.0, 0.0, ""))

    def test_substitution_replaces(self):
        s = ObstaclePulseState()
        s.ingest_new_message({"obstacle": True, "intensity": -0.5}, now=10.0)
        s.ingest_new_message({"obstacle": True, "intensity": 0.8}, now=10.3)
        self.assertAlmostEqual(s.intensity, 0.8)
        self.assertAlmostEqual(s.last_payload_ts, 10.3)

    def test_zero_intensity_is_no_op(self):
        """obstacle=true pero intensity=0 → idle (no aplica esquive)."""
        s = ObstaclePulseState()
        s.ingest_new_message({"obstacle": True, "intensity": 0.0}, now=10.0)
        self.assertFalse(s.active)
        a, c, st = s.get_offsets(now=10.1, carstate=_carstate(), lat_active=True)
        self.assertEqual(st, "")
        self.assertEqual(a, 0.0)
        self.assertEqual(c, 0.0)


if __name__ == "__main__":
    unittest.main()
