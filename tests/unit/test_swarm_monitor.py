"""Unit tests for swarm monitor."""
import pytest
from monitor.swarm_monitor import SwarmMonitor
from drones.types import DroneState, DroneMode, DroneAlert, GeoPoint, AlertSeverity, AlertType


def make_state(drone_id, mode, battery_pct=80.0, lat=37.3861, lon=-122.0839):
    return DroneState(
        drone_id=drone_id,
        mode=int(mode),
        battery_pct=battery_pct,
        position=GeoPoint(latitude=lat, longitude=lon, altitude_m=50.0),
    )


class TestModeCounts:
    def test_counts_active_drones(self):
        mon = SwarmMonitor()
        mon.update_drone_state(make_state(0, DroneMode.EN_ROUTE))
        mon.update_drone_state(make_state(1, DroneMode.EN_ROUTE))
        mon.update_drone_state(make_state(2, DroneMode.HOVERING))
        summary = mon.compute_summary()
        assert summary.active_drones == 3

    def test_counts_faulted(self):
        mon = SwarmMonitor()
        mon.update_drone_state(make_state(0, DroneMode.FAULT))
        summary = mon.compute_summary()
        assert summary.faulted_drones == 1

    def test_counts_returning(self):
        mon = SwarmMonitor()
        mon.update_drone_state(make_state(0, DroneMode.RETURNING_TO_BASE))
        summary = mon.compute_summary()
        assert summary.returning_drones == 1

    def test_counts_idle(self):
        mon = SwarmMonitor()
        mon.update_drone_state(make_state(0, DroneMode.IDLE))
        mon.update_drone_state(make_state(1, DroneMode.LANDED))
        summary = mon.compute_summary()
        assert summary.idle_drones == 2

    def test_full_swarm_scenario(self):
        """SPEC section 9 scenario."""
        mon = SwarmMonitor()
        modes = [
            DroneMode.EN_ROUTE, DroneMode.EN_ROUTE, DroneMode.RETURNING_TO_BASE,
            DroneMode.EN_ROUTE, DroneMode.FAULT, DroneMode.EN_ROUTE,
            DroneMode.EN_ROUTE, DroneMode.IDLE
        ]
        for i, mode in enumerate(modes):
            mon.update_drone_state(make_state(i, mode))
        summary = mon.compute_summary()
        assert summary.active_drones == 5
        assert summary.faulted_drones == 1
        assert summary.returning_drones == 1
        assert summary.idle_drones == 1
        assert summary.total_drones == 8


class TestBatteryStats:
    def test_avg_battery(self):
        mon = SwarmMonitor()
        batteries = [85, 72, 31, 90, 65, 88, 55, 100]
        for i, bat in enumerate(batteries):
            mon.update_drone_state(make_state(i, DroneMode.EN_ROUTE, battery_pct=bat))
        summary = mon.compute_summary()
        assert abs(summary.avg_battery_pct - 73.25) < 0.1

    def test_min_battery(self):
        mon = SwarmMonitor()
        batteries = [85, 72, 31, 90, 65, 88, 55, 100]
        for i, bat in enumerate(batteries):
            mon.update_drone_state(make_state(i, DroneMode.EN_ROUTE, battery_pct=bat))
        summary = mon.compute_summary()
        assert summary.min_battery_pct == 31.0
        assert summary.min_battery_drone_id == 2


class TestDistanceTracking:
    def test_distance_accumulates(self):
        mon = SwarmMonitor()
        # Move drone 0 north
        mon.update_drone_state(make_state(0, DroneMode.EN_ROUTE, lat=37.3861, lon=-122.0839))
        mon.update_drone_state(make_state(0, DroneMode.EN_ROUTE, lat=37.3871, lon=-122.0839))
        summary = mon.compute_summary()
        assert summary.total_distance_covered_m > 100  # ~111m


class TestAlertTracking:
    def test_alert_counting(self):
        mon = SwarmMonitor()
        mon.update_drone_state(make_state(0, DroneMode.EN_ROUTE))
        alert = DroneAlert(
            drone_id=0, alert_seq=1,
            alert_type=int(AlertType.MOTOR_FAULT),
            severity=int(AlertSeverity.WARNING),
            message="test",
            acknowledged=False,
        )
        mon.update_alert(alert)
        summary = mon.compute_summary()
        assert summary.active_alerts == 1
