"""Mission planner — generates and assigns missions for the drone swarm."""
from drones.types import MissionPlan, GeoPoint
from mission.mission_patterns import (
    perimeter_patrol, grid_north, grid_south,
    radial_survey, diagonal_cross, circle_patrol, point_inspection
)
import time


MISSION_ASSIGNMENTS = {
    0: ("Perimeter Patrol", perimeter_patrol, 50.0, 10.0),
    1: ("Grid Search North", grid_north, 50.0, 12.0),
    2: ("Grid Search South", grid_south, 50.0, 10.0),
    3: ("Radial Survey", radial_survey, 60.0, 10.0),
    4: ("Diagonal Cross", diagonal_cross, 55.0, 10.0),
    5: ("Circle Patrol", circle_patrol, 45.0, 8.0),
    6: ("Point Inspection", point_inspection, 70.0, 13.0),
    # 7: No mission (HOTEL stays idle)
}


def generate_missions():
    """Generate MissionPlan objects for drones 0-6. Drone 7 gets no mission."""
    missions = {}
    for drone_id, (name, pattern_fn, altitude, speed) in MISSION_ASSIGNMENTS.items():
        waypoint_dicts = pattern_fn(altitude)
        waypoints = [
            GeoPoint(latitude=wp["latitude"], longitude=wp["longitude"], altitude_m=wp["altitude_m"])
            for wp in waypoint_dicts
        ]
        mission = MissionPlan(
            drone_id=drone_id,
            timestamp_ns=int(time.time() * 1e9),
            waypoint_count=len(waypoints),
            waypoints=waypoints,
            cruise_speed_mps=speed,
            cruise_altitude_m=altitude,
            is_active=True,
            mission_name=name,
        )
        missions[drone_id] = mission
    return missions
