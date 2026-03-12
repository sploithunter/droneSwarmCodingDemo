"""Unit tests for mission planner."""
import pytest
from mission.mission_planner import generate_missions


def test_generates_7_missions():
    missions = generate_missions()
    assert len(missions) == 7


def test_drone_7_excluded():
    missions = generate_missions()
    assert 7 not in missions


def test_all_missions_active():
    missions = generate_missions()
    for drone_id, mission in missions.items():
        assert mission.is_active is True, f"Drone {drone_id} mission not active"


def test_all_missions_have_names():
    missions = generate_missions()
    for drone_id, mission in missions.items():
        assert mission.mission_name, f"Drone {drone_id} mission has no name"


def test_waypoint_counts_match():
    missions = generate_missions()
    for drone_id, mission in missions.items():
        assert mission.waypoint_count == len(mission.waypoints), (
            f"Drone {drone_id}: waypoint_count={mission.waypoint_count} "
            f"but len(waypoints)={len(mission.waypoints)}"
        )


def test_correct_pattern_assignments():
    """Verify waypoint counts match expected: 8,12,12,8,6,16,4."""
    expected = {0: 8, 1: 12, 2: 12, 3: 8, 4: 6, 5: 16, 6: 4}
    missions = generate_missions()
    for drone_id, count in expected.items():
        assert len(missions[drone_id].waypoints) == count, (
            f"Drone {drone_id}: expected {count} waypoints, "
            f"got {len(missions[drone_id].waypoints)}"
        )
