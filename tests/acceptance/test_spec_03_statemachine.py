"""Acceptance tests for SPEC section 3 — State Machine."""
import pytest
from drones.drone_sim import DroneSim
from drones.types import (
    DroneMode, DroneCommand, CommandType, MissionPlan, GeoPoint,
    AlertType, AlertSeverity
)
from drones.drone_config import BASE_STATION


def make_mission(drone_id=0, altitude=50.0, speed=10.0):
    waypoints = [
        GeoPoint(37.387, -122.084, altitude),
        GeoPoint(37.387, -122.083, altitude),
        GeoPoint(37.385, -122.083, altitude),
        GeoPoint(37.385, -122.084, altitude),
    ]
    return MissionPlan(
        drone_id=drone_id,
        waypoint_count=len(waypoints),
        waypoints=waypoints,
        cruise_speed_mps=speed,
        cruise_altitude_m=altitude,
        is_active=True,
        mission_name="Test",
    )


def make_cmd(drone_id, command, **kwargs):
    return DroneCommand(
        drone_id=drone_id,
        command=int(command),
        parameter=kwargs.get("parameter", 0.0),
        target_position=kwargs.get("target", GeoPoint()),
    )


class TestSpec31Startup:
    def test_drone_starts_idle(self):
        sim = DroneSim(0, rng_seed=42)
        assert sim.mode == DroneMode.IDLE

    def test_drone_at_base_station(self):
        sim = DroneSim(0, rng_seed=42)
        state = sim.tick(0.1)
        assert abs(state.position.latitude - BASE_STATION[0]) < 0.001
        assert abs(state.position.longitude - BASE_STATION[1]) < 0.001

    def test_drone_altitude_zero(self):
        sim = DroneSim(0, rng_seed=42)
        state = sim.tick(0.1)
        assert state.position.altitude_m == 0.0


class TestSpec32MissionActivation:
    def test_idle_to_takeoff_on_mission(self):
        sim = DroneSim(0, rng_seed=42)
        sim.set_mission(make_mission())
        assert sim.mode == DroneMode.TAKEOFF

    def test_takeoff_to_en_route_at_altitude(self):
        sim = DroneSim(0, rng_seed=42)
        sim.set_mission(make_mission(altitude=5.0))
        for _ in range(50):
            sim.tick(0.1)
        assert sim.mode == DroneMode.EN_ROUTE


class TestSpec33WaypointNavigation:
    def test_waypoint_idx_preserved_on_hover(self):
        sim = DroneSim(0, rng_seed=42)
        sim.mode = DroneMode.EN_ROUTE
        sim.current_waypoint_idx = 3
        sim.handle_command(make_cmd(0, CommandType.HOVER))
        assert sim.mode == DroneMode.HOVERING
        assert sim.current_waypoint_idx == 3


class TestSpec34CommandHandling:
    def test_hover_pauses(self):
        sim = DroneSim(0, rng_seed=42)
        sim.mode = DroneMode.EN_ROUTE
        sim.handle_command(make_cmd(0, CommandType.HOVER))
        assert sim.mode == DroneMode.HOVERING

    def test_resume_from_hover(self):
        sim = DroneSim(0, rng_seed=42)
        sim.mode = DroneMode.HOVERING
        sim.handle_command(make_cmd(0, CommandType.RESUME_MISSION))
        assert sim.mode == DroneMode.EN_ROUTE

    def test_rtb_command(self):
        sim = DroneSim(0, rng_seed=42)
        sim.mode = DroneMode.EN_ROUTE
        sim.handle_command(make_cmd(0, CommandType.RETURN_TO_BASE))
        assert sim.mode == DroneMode.RETURNING_TO_BASE

    def test_emergency_land(self):
        sim = DroneSim(0, rng_seed=42)
        sim.mode = DroneMode.EN_ROUTE
        sim.handle_command(make_cmd(0, CommandType.EMERGENCY_LAND))
        assert sim.mode == DroneMode.LANDING

    def test_set_speed(self):
        sim = DroneSim(0, rng_seed=42)
        sim.handle_command(make_cmd(0, CommandType.SET_SPEED, parameter=13.0))
        assert sim.cruise_speed == 13.0

    def test_set_altitude(self):
        sim = DroneSim(0, rng_seed=42)
        sim.handle_command(make_cmd(0, CommandType.SET_ALTITUDE, parameter=80.0))
        assert sim.cruise_altitude == 80.0

    def test_broadcast_affects_all(self):
        sim = DroneSim(0, rng_seed=42)
        sim.mode = DroneMode.EN_ROUTE
        sim.handle_command(make_cmd(255, CommandType.HOVER))
        assert sim.mode == DroneMode.HOVERING


class TestSpec35Landing:
    def test_landing_to_idle(self):
        sim = DroneSim(0, rng_seed=42)
        sim.mode = DroneMode.LANDING
        sim.physics.altitude = 0.3
        sim.tick(0.1)
        assert sim.mode == DroneMode.IDLE

    def test_motor_rpms_zero_on_idle(self):
        sim = DroneSim(0, rng_seed=42)
        state = sim.tick(0.1)
        assert all(rpm == 0.0 for rpm in state.motor_rpm)
