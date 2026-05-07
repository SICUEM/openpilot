"""Tests unitarios del esquive de obstáculos (modo 3 COMMA+JETSON)."""
import unittest
from unittest.mock import MagicMock

from openpilot.sicuem.adripilot.adripilot_obstacle_pulse import (
    ObstaclePulseState,
    DEFAULT_MAX_DURATION_MS,
    DEFAULT_WATCHDOG_MS,
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
        s.ingest_new_message({"obstacle": True, "intensity": 0.4, "duration_ms": 1000}, now=10.0)
        self.assertTrue(s.active)
        self.assertAlmostEqual(s.intensity, 0.4)
        self.assertAlmostEqual(s.duration_s, 1.0)

    def test_offsets_proportional_to_intensity(self):
        s = ObstaclePulseState()
        s.ingest_new_message({"obstacle": True, "intensity": -0.5, "duration_ms": 1000}, now=10.0)
        a, c, st = s.get_offsets(now=10.3, carstate=_carstate(), lat_active=True)  # 300ms gap < 400ms watchdog
        self.assertAlmostEqual(a, -0.5 * DEFAULT_MAX_ANGLE)
        self.assertAlmostEqual(c, -0.5 * DEFAULT_MAX_CURV)
        self.assertEqual(st, "DODGING_RIGHT")

    def test_offsets_left_status(self):
        s = ObstaclePulseState()
        s.ingest_new_message({"obstacle": True, "intensity": 0.7, "duration_ms": 1000}, now=10.0)
        a, c, st = s.get_offsets(now=10.3, carstate=_carstate(), lat_active=True)
        self.assertGreater(a, 0)
        self.assertGreater(c, 0)
        self.assertEqual(st, "DODGING_LEFT")

    def test_natural_expiration(self):
        s = ObstaclePulseState()
        s.ingest_new_message({"obstacle": True, "intensity": -0.5, "duration_ms": 1000}, now=10.0)
        # En t=10.3 sigue activo (300ms < watchdog 400ms, 300ms < dur 1000ms)
        a, _, _ = s.get_offsets(now=10.3, carstate=_carstate(), lat_active=True)
        self.assertNotEqual(a, 0)
        # En t=11.1 expira por duración (1100ms > dur 1000ms) ANTES que por watchdog
        # → debe devolver "" (idle), no CANCELED_STALE
        a, c, st = s.get_offsets(now=11.1, carstate=_carstate(), lat_active=True)
        self.assertEqual((a, c, st), (0.0, 0.0, ""))
        self.assertFalse(s.active)

    def test_cancel_steering_pressed(self):
        s = ObstaclePulseState()
        s.ingest_new_message({"obstacle": True, "intensity": -0.5, "duration_ms": 1000}, now=10.0)
        a, c, st = s.get_offsets(now=10.3, carstate=_carstate(steering_pressed=True), lat_active=True)
        self.assertEqual((a, c), (0.0, 0.0))
        self.assertEqual(st, "CANCELED_DRIVER")
        self.assertFalse(s.active)

    def test_cancel_brake_pressed(self):
        s = ObstaclePulseState()
        s.ingest_new_message({"obstacle": True, "intensity": 0.5, "duration_ms": 1000}, now=10.0)
        _, _, st = s.get_offsets(now=10.3, carstate=_carstate(brake_pressed=True), lat_active=True)
        self.assertEqual(st, "CANCELED_DRIVER")

    def test_cancel_watchdog_stale(self):
        s = ObstaclePulseState()
        # dur=2000ms, gap=500ms → 500 > watchdog 400 → STALE (y dur no ha expirado)
        s.ingest_new_message({"obstacle": True, "intensity": -0.5, "duration_ms": 2000}, now=10.0)
        _, _, st = s.get_offsets(now=10.5, carstate=_carstate(), lat_active=True)
        self.assertEqual(st, "CANCELED_STALE")

    def test_cancel_lat_inactive(self):
        s = ObstaclePulseState()
        s.ingest_new_message({"obstacle": True, "intensity": -0.5, "duration_ms": 1000}, now=10.0)
        a, c, st = s.get_offsets(now=10.3, carstate=_carstate(), lat_active=False)
        self.assertEqual((a, c, st), (0.0, 0.0, ""))
        self.assertFalse(s.active)

    def test_clamp_intensity(self):
        s = ObstaclePulseState()
        s.ingest_new_message({"obstacle": True, "intensity": 99.0, "duration_ms": 500}, now=0.0)
        self.assertEqual(s.intensity, 1.0)
        s.ingest_new_message({"obstacle": True, "intensity": -99.0, "duration_ms": 500}, now=0.0)
        self.assertEqual(s.intensity, -1.0)

    def test_cap_duration(self):
        s = ObstaclePulseState()
        s.ingest_new_message(
            {"obstacle": True, "intensity": 0.5, "duration_ms": 999999},
            now=0.0,
            max_duration_ms=2500.0,
        )
        self.assertAlmostEqual(s.duration_s, 2.5)

    def test_obstacle_false_cancels(self):
        s = ObstaclePulseState()
        s.ingest_new_message({"obstacle": True, "intensity": -0.5, "duration_ms": 1000}, now=10.0)
        self.assertTrue(s.active)
        s.ingest_new_message({"obstacle": False, "intensity": 0.0, "duration_ms": 0}, now=10.2)
        self.assertFalse(s.active)

    def test_substitution_replaces(self):
        s = ObstaclePulseState()
        s.ingest_new_message({"obstacle": True, "intensity": -0.5, "duration_ms": 1000}, now=10.0)
        s.ingest_new_message({"obstacle": True, "intensity": 0.8, "duration_ms": 1500}, now=10.3)
        self.assertAlmostEqual(s.intensity, 0.8)
        self.assertAlmostEqual(s.duration_s, 1.5)
        self.assertAlmostEqual(s.start_ts, 10.3)


if __name__ == "__main__":
    unittest.main()
