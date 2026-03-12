"""Unit tests for drones.flight_physics module."""
import math
import pytest
from drones.flight_physics import (
    FlightPhysics,
    haversine_distance,
    calculate_bearing,
    normalize_angle,
    METERS_PER_DEG_LAT,
)
from drones.drone_config import MAX_SPEED, ASCENT_RATE, DESCENT_RATE, TURN_RATE, ACCELERATION, MAX_ALTITUDE


# ── Bearing tests ──────────────────────────────────────────────

def test_bearing_north():
    """Bearing from (0,0) to (1,0) should be ~0 degrees (north)."""
    b = calculate_bearing(0, 0, 1, 0)
    assert abs(b - 0) < 1.0 or abs(b - 360) < 1.0


def test_bearing_east():
    """Bearing from (0,0) to (0,1) should be ~90 degrees (east)."""
    b = calculate_bearing(0, 0, 0, 1)
    assert abs(b - 90) < 1.0


def test_bearing_south():
    """Bearing from (1,0) to (0,0) should be ~180 degrees (south)."""
    b = calculate_bearing(1, 0, 0, 0)
    assert abs(b - 180) < 1.0


def test_bearing_west():
    """Bearing from (0,0) to (0,-1) should be ~270 degrees (west)."""
    b = calculate_bearing(0, 0, 0, -1)
    assert abs(b - 270) < 1.0


# ── Haversine tests ───────────────────────────────────────────

def test_haversine_distance():
    """1 degree latitude ≈ 111 km."""
    d = haversine_distance(0, 0, 1, 0)
    assert 111_000 < d < 111_400


def test_haversine_zero():
    """Same point should give 0 distance."""
    d = haversine_distance(37.0, -122.0, 37.0, -122.0)
    assert d == pytest.approx(0.0, abs=1e-6)


# ── Heading rate bounded ──────────────────────────────────────

def test_heading_rate_bounded():
    """Heading change per 0.1s tick <= TURN_RATE * 0.1 = 4.5 degrees."""
    fp = FlightPhysics(lat=0.0, lon=0.0, heading=0.0)
    # Target is due west — requires ~270 deg turn (or -90 short path)
    fp.update(0.1, target_waypoint=(0.0, -1.0), target_altitude=0.0)
    heading_change = abs(fp.heading - 0.0)
    # Could have wrapped, take min
    heading_change = min(heading_change, 360 - heading_change)
    assert heading_change <= TURN_RATE * 0.1 + 0.01


# ── Speed bounded ─────────────────────────────────────────────

def test_speed_bounded_by_max():
    """Speed should never exceed MAX_SPEED even with high cruise_speed."""
    fp = FlightPhysics(lat=0.0, lon=0.0, heading=0.0)
    # Run many ticks with high cruise speed toward a far waypoint
    for _ in range(1000):
        fp.update(0.1, target_waypoint=(1.0, 0.0), cruise_speed=100.0)
    assert fp.speed <= MAX_SPEED


# ── Acceleration bounded ──────────────────────────────────────

def test_acceleration_bounded():
    """Speed increase per 0.1s tick <= ACCELERATION * 0.1 = 0.3 m/s."""
    fp = FlightPhysics(lat=0.0, lon=0.0, heading=0.0)
    fp.update(0.1, target_waypoint=(1.0, 0.0), cruise_speed=15.0)
    assert fp.speed <= ACCELERATION * 0.1 + 1e-9


# ── Vertical rates ────────────────────────────────────────────

def test_ascent_rate():
    """Drone should ascend at ASCENT_RATE (3 m/s)."""
    fp = FlightPhysics(lat=0.0, lon=0.0, altitude=0.0)
    fp.update(1.0, target_altitude=100.0)
    assert fp.altitude == pytest.approx(ASCENT_RATE, abs=0.5)


def test_descent_rate():
    """Drone should descend at DESCENT_RATE (2 m/s)."""
    fp = FlightPhysics(lat=0.0, lon=0.0, altitude=100.0)
    fp.update(1.0, target_altitude=0.0)
    assert fp.altitude == pytest.approx(100.0 - DESCENT_RATE, abs=0.5)


def test_altitude_capped():
    """Altitude should never exceed MAX_ALTITUDE (120m)."""
    fp = FlightPhysics(lat=0.0, lon=0.0, altitude=119.0)
    for _ in range(100):
        fp.update(0.1, target_altitude=200.0)
    assert fp.altitude <= MAX_ALTITUDE


# ── Deceleration near waypoint ────────────────────────────────

def test_deceleration_near_waypoint():
    """Speed should decrease when within 50m of waypoint."""
    fp = FlightPhysics(lat=0.0, lon=0.0, heading=0.0)
    # Build up speed toward a far waypoint
    for _ in range(200):
        fp.update(0.1, target_waypoint=(1.0, 0.0), cruise_speed=10.0)
    fast_speed = fp.speed

    # Now set a waypoint very close (within 50m)
    close_lat = fp.lat + 20.0 / METERS_PER_DEG_LAT  # ~20m north
    for _ in range(10):
        fp.update(0.1, target_waypoint=(close_lat, fp.lon), cruise_speed=10.0)
    assert fp.speed < fast_speed


# ── Waypoint reached ──────────────────────────────────────────

def test_waypoint_reached_detection():
    """Returns True when within 5m horiz and 2m vert of waypoint."""
    # Place drone almost on top of the waypoint
    target = (0.0001, 0.0)  # very close to origin
    fp = FlightPhysics(lat=0.0001, lon=0.0, altitude=50.0, heading=0.0)
    reached, dist = fp.update(0.1, target_waypoint=target, target_altitude=50.0)
    # Distance should be ~0m
    assert dist < 5.0
    assert reached is True


# ── Position update directions ────────────────────────────────

def test_position_updates_northward():
    """Latitude should increase when heading north with speed."""
    fp = FlightPhysics(lat=0.0, lon=0.0, heading=0.0)
    fp.speed = 10.0
    initial_lat = fp.lat
    fp.update(1.0, target_waypoint=(1.0, 0.0), cruise_speed=10.0)
    assert fp.lat > initial_lat


def test_position_updates_eastward():
    """Longitude should increase when heading east with speed."""
    fp = FlightPhysics(lat=0.0, lon=0.0001, heading=90.0)
    fp.speed = 10.0
    initial_lon = fp.lon
    fp.update(1.0, target_waypoint=(0.0, 1.0), cruise_speed=10.0)
    assert fp.lon > initial_lon


# ── Stop when no waypoint ─────────────────────────────────────

def test_stop_when_no_waypoint():
    """Drone should decelerate to 0 when no target waypoint is given."""
    fp = FlightPhysics(lat=0.0, lon=0.0, heading=0.0)
    fp.speed = 10.0
    for _ in range(200):
        fp.update(0.1)
    assert fp.speed == pytest.approx(0.0, abs=1e-9)
