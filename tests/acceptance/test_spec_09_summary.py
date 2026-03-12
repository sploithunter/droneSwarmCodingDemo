"""Acceptance tests for SPEC section 9 — Swarm Summary."""
import pytest
from monitor.swarm_monitor import SwarmMonitor
from drones.types import DroneState, DroneMode, GeoPoint


def make_state(drone_id, mode, battery_pct=80.0):
    return DroneState(
        drone_id=drone_id,
        mode=int(mode),
        battery_pct=battery_pct,
        position=GeoPoint(latitude=37.3861, longitude=-122.0839, altitude_m=50.0),
    )


class TestSpec09Summary:
    def test_mode_counts(self):
        """SPEC: active=5, faulted=1, returning=1, idle=1."""
        mon = SwarmMonitor()
        modes = [
            DroneMode.EN_ROUTE, DroneMode.EN_ROUTE, DroneMode.RETURNING_TO_BASE,
            DroneMode.EN_ROUTE, DroneMode.FAULT, DroneMode.EN_ROUTE,
            DroneMode.EN_ROUTE, DroneMode.IDLE
        ]
        for i, mode in enumerate(modes):
            mon.update_drone_state(make_state(i, mode))
        s = mon.compute_summary()
        assert s.active_drones == 5
        assert s.faulted_drones == 1
        assert s.returning_drones == 1
        assert s.idle_drones == 1
        assert s.total_drones == 8

    def test_battery_stats(self):
        """SPEC: avg ~73.25%, min 31% drone 2."""
        mon = SwarmMonitor()
        batteries = [85, 72, 31, 90, 65, 88, 55, 100]
        for i, bat in enumerate(batteries):
            mon.update_drone_state(make_state(i, DroneMode.EN_ROUTE, battery_pct=bat))
        s = mon.compute_summary()
        assert abs(s.avg_battery_pct - 73.25) < 0.1
        assert s.min_battery_pct == 31.0
        assert s.min_battery_drone_id == 2

    def test_summary_id_zero(self):
        mon = SwarmMonitor()
        mon.update_drone_state(make_state(0, DroneMode.IDLE))
        s = mon.compute_summary()
        assert s.summary_id == 0

    def test_timestamp_positive(self):
        mon = SwarmMonitor()
        mon.update_drone_state(make_state(0, DroneMode.IDLE))
        s = mon.compute_summary()
        assert s.timestamp_ns > 0
