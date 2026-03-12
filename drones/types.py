"""DDS Drone Swarm data types.

Implements all IDL-defined types as Python dataclasses with optional
RTI Connext DDS type support via rti.types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum

# Attempt to import RTI Connext type decorators; fall back to plain dataclass.
try:
    import rti.types as idl
    _has_rti = True
except ImportError:
    _has_rti = False


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class DroneMode(IntEnum):
    IDLE = 0
    TAKEOFF = 1
    EN_ROUTE = 2
    HOVERING = 3
    RETURNING_TO_BASE = 4
    LANDING = 5
    LANDED = 6
    FAULT = 7


class AlertSeverity(IntEnum):
    INFO = 0
    WARNING = 1
    CRITICAL = 2


class AlertType(IntEnum):
    LOW_BATTERY = 0
    GEOFENCE_BREACH = 1
    COLLISION_WARNING = 2
    MOTOR_FAULT = 3
    GPS_DEGRADED = 4
    COMMUNICATION_TIMEOUT = 5
    MISSION_COMPLETE = 6


class CommandType(IntEnum):
    GOTO_WAYPOINT = 0
    RETURN_TO_BASE = 1
    HOVER = 2
    RESUME_MISSION = 3
    EMERGENCY_LAND = 4
    SET_SPEED = 5
    SET_ALTITUDE = 6


# ---------------------------------------------------------------------------
# Coordinate Types
# ---------------------------------------------------------------------------

@dataclass
class GeoPoint:
    latitude: float = 0.0
    longitude: float = 0.0
    altitude_m: float = 0.0


@dataclass
class Vector3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


# ---------------------------------------------------------------------------
# Primary Data Types
# ---------------------------------------------------------------------------

@dataclass
class DroneState:
    drone_id: int = 0
    timestamp_ns: int = 0
    position: GeoPoint = field(default_factory=GeoPoint)
    heading_deg: float = 0.0
    velocity: Vector3 = field(default_factory=Vector3)
    ground_speed_mps: float = 0.0
    mode: int = 0
    battery_pct: float = 0.0
    battery_voltage: float = 0.0
    signal_strength_dbm: float = 0.0
    current_waypoint_idx: int = 0
    total_waypoints: int = 0
    mission_progress_pct: float = 0.0
    motor_rpm: list = field(default_factory=lambda: [0.0] * 4)
    internal_temp_c: float = 0.0
    gps_satellite_count: int = 0
    gps_hdop: float = 0.0


@dataclass
class DroneCommand:
    drone_id: int = 0
    timestamp_ns: int = 0
    command: int = 0
    target_position: GeoPoint = field(default_factory=GeoPoint)
    parameter: float = 0.0
    command_seq: int = 0
    issuer: str = ""


@dataclass
class DroneAlert:
    drone_id: int = 0
    alert_seq: int = 0
    timestamp_ns: int = 0
    alert_type: int = 0
    severity: int = 0
    message: str = ""
    position: GeoPoint = field(default_factory=GeoPoint)
    battery_pct: float = 0.0
    drone_mode: int = 0
    acknowledged: bool = False


@dataclass
class MissionPlan:
    drone_id: int = 0
    timestamp_ns: int = 0
    waypoint_count: int = 0
    waypoints: list = field(default_factory=list)
    cruise_speed_mps: float = 0.0
    cruise_altitude_m: float = 0.0
    is_active: bool = False
    mission_name: str = ""


@dataclass
class SwarmSummary:
    summary_id: int = 0
    timestamp_ns: int = 0
    total_drones: int = 0
    active_drones: int = 0
    faulted_drones: int = 0
    returning_drones: int = 0
    idle_drones: int = 0
    avg_battery_pct: float = 0.0
    min_battery_pct: float = 0.0
    min_battery_drone_id: int = 0
    total_distance_covered_m: float = 0.0
    active_alerts: int = 0
    missions_completed: int = 0
