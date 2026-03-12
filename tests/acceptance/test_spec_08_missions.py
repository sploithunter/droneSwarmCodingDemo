"""Acceptance tests for SPEC 8: Mission patterns and planning."""
import pytest
from mission.mission_patterns import (
    CENTER_LAT, CENTER_LON, HALF_LAT, HALF_LON,
    perimeter_patrol, grid_north, grid_south,
)
from mission.mission_planner import generate_missions


class TestSpec8_1_MissionPatterns:
    """SPEC 8.1: perimeter has 8 wp, grid has 12 wp, all within geofence."""

    def test_perimeter_has_8_waypoints(self):
        assert len(perimeter_patrol()) == 8

    def test_grid_north_has_12_waypoints(self):
        assert len(grid_north()) == 12

    def test_grid_south_has_12_waypoints(self):
        assert len(grid_south()) == 12

    def test_all_waypoints_within_geofence(self):
        """All pattern waypoints must stay within the operational area."""
        lat_limit = HALF_LAT * 1.0  # full half-size as geofence
        lon_limit = HALF_LON * 1.0
        for pattern_fn in [perimeter_patrol, grid_north, grid_south]:
            for wp in pattern_fn():
                assert abs(wp["latitude"] - CENTER_LAT) <= lat_limit, (
                    f"{pattern_fn.__name__}: lat out of geofence"
                )
                assert abs(wp["longitude"] - CENTER_LON) <= lon_limit, (
                    f"{pattern_fn.__name__}: lon out of geofence"
                )


class TestSpec8_2_MissionPlanning:
    """SPEC 8.2: missions published for drones 0-6, all active, drone 7 gets none."""

    def test_missions_for_drones_0_through_6(self):
        missions = generate_missions()
        for drone_id in range(7):
            assert drone_id in missions, f"Drone {drone_id} missing mission"

    def test_all_missions_active(self):
        missions = generate_missions()
        for drone_id, mission in missions.items():
            assert mission.is_active is True

    def test_drone_7_gets_no_mission(self):
        missions = generate_missions()
        assert 7 not in missions
