"""Acceptance tests for SPEC-04: Flight Physics."""
import math
import pytest
from drones.flight_physics import FlightPhysics, haversine_distance
from drones.drone_config import MAX_SPEED, ASCENT_RATE, DESCENT_RATE, TURN_RATE, ACCELERATION, MAX_ALTITUDE


class TestSpec4_1_KinematicModel:
    """SPEC 4.1 — position updates at 10 Hz; heading, speed, acceleration bounded."""

    def test_position_updates_at_10hz(self):
        """Position should change after a 0.1s tick with speed > 0."""
        fp = FlightPhysics(lat=0.0, lon=0.0, heading=0.0)
        fp.speed = 10.0
        lat0 = fp.lat
        fp.update(0.1, target_waypoint=(1.0, 0.0), cruise_speed=10.0)
        assert fp.lat != lat0, "Position must change at 10 Hz tick"

    def test_heading_adjustment_bounded_by_turn_rate(self):
        """Heading change per tick must not exceed TURN_RATE * dt."""
        fp = FlightPhysics(lat=0.0, lon=0.0, heading=0.0)
        dt = 0.1
        # Target bearing is roughly 270 (west), so diff = -90
        fp.update(dt, target_waypoint=(0.0, -1.0), target_altitude=0.0)
        heading_change = min(abs(fp.heading), 360 - abs(fp.heading))
        assert heading_change <= TURN_RATE * dt + 0.01

    def test_speed_bounded_by_max_speed(self):
        """Speed must never exceed MAX_SPEED regardless of cruise_speed."""
        fp = FlightPhysics(lat=0.0, lon=0.0, heading=0.0)
        for _ in range(2000):
            fp.update(0.1, target_waypoint=(10.0, 0.0), cruise_speed=999.0)
        assert fp.speed <= MAX_SPEED

    def test_acceleration_bounded_per_tick(self):
        """Speed increase from rest must not exceed ACCELERATION * dt."""
        fp = FlightPhysics(lat=0.0, lon=0.0, heading=0.0)
        dt = 0.1
        fp.update(dt, target_waypoint=(1.0, 0.0), cruise_speed=15.0)
        assert fp.speed <= ACCELERATION * dt + 1e-9

    def test_multiple_ticks_speed_ramp(self):
        """After N ticks, speed <= ACCELERATION * dt * N (linear ramp)."""
        fp = FlightPhysics(lat=0.0, lon=0.0, heading=0.0)
        dt = 0.1
        n = 10
        for _ in range(n):
            fp.update(dt, target_waypoint=(1.0, 0.0), cruise_speed=15.0)
        assert fp.speed <= ACCELERATION * dt * n + 1e-6


class TestSpec4_2_VerticalRates:
    """SPEC 4.2 — ascent 3 m/s, descent 2 m/s, altitude capped at 120 m."""

    def test_ascent_rate_3mps(self):
        """Ascending drone should climb at ASCENT_RATE (3 m/s)."""
        fp = FlightPhysics(lat=0.0, lon=0.0, altitude=0.0)
        dt = 1.0
        fp.update(dt, target_altitude=100.0)
        assert fp.altitude == pytest.approx(ASCENT_RATE * dt, abs=0.5)

    def test_descent_rate_2mps(self):
        """Descending drone should descend at DESCENT_RATE (2 m/s)."""
        fp = FlightPhysics(lat=0.0, lon=0.0, altitude=100.0)
        dt = 1.0
        fp.update(dt, target_altitude=0.0)
        expected = 100.0 - DESCENT_RATE * dt
        assert fp.altitude == pytest.approx(expected, abs=0.5)

    def test_altitude_capped_at_max(self):
        """Altitude must never exceed MAX_ALTITUDE (120 m)."""
        fp = FlightPhysics(lat=0.0, lon=0.0, altitude=0.0)
        for _ in range(500):
            fp.update(0.1, target_altitude=500.0)
        assert fp.altitude <= MAX_ALTITUDE

    def test_altitude_floor_at_zero(self):
        """Altitude must never go below 0."""
        fp = FlightPhysics(lat=0.0, lon=0.0, altitude=1.0)
        for _ in range(500):
            fp.update(0.1, target_altitude=-100.0)
        assert fp.altitude >= 0.0

    def test_ascent_then_cap(self):
        """Ascend to well above MAX_ALTITUDE; verify cap is enforced."""
        fp = FlightPhysics(lat=0.0, lon=0.0, altitude=118.0)
        for _ in range(100):
            fp.update(0.1, target_altitude=200.0)
        assert fp.altitude == pytest.approx(MAX_ALTITUDE, abs=0.1)
