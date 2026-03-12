"""DDS Drone Swarm data types.

Implements all IDL-defined types as Python dataclasses with optional
RTI Connext DDS type support via rti.types.
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Sequence

# Attempt to import RTI Connext type decorators; fall back to plain dataclass.
try:
    import rti.types as idl
    _has_rti = True
except ImportError:
    _has_rti = False


def _dds_type(cls=None, *, member_annotations=None):
    """Decorator: @idl.struct when RTI available, @dataclass otherwise."""
    def wrap(c):
        if _has_rti:
            if member_annotations:
                return idl.struct(member_annotations=member_annotations)(c)
            return idl.struct(c)
        return dataclass(c)
    if cls is not None:
        return wrap(cls)
    return wrap


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

@_dds_type
class GeoPoint:
    latitude: float = 0.0
    longitude: float = 0.0
    altitude_m: float = 0.0


@_dds_type
class Vector3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


# ---------------------------------------------------------------------------
# DDS member annotations (only constructed when RTI is available)
# ---------------------------------------------------------------------------

if _has_rti:
    _STATE_ANN = {'drone_id': [idl.key]}
    _CMD_ANN = {'drone_id': [idl.key], 'issuer': [idl.bound(128)]}
    _ALERT_ANN = {'drone_id': [idl.key], 'message': [idl.bound(256)]}
    _MISSION_ANN = {'drone_id': [idl.key], 'mission_name': [idl.bound(128)]}
    _motor_rpm_factory = idl.array_factory(float, [4])
else:
    _STATE_ANN = None
    _CMD_ANN = None
    _ALERT_ANN = None
    _MISSION_ANN = None
    _motor_rpm_factory = lambda: [0.0] * 4


# ---------------------------------------------------------------------------
# Primary Data Types
# ---------------------------------------------------------------------------

@_dds_type(member_annotations=_STATE_ANN)
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
    motor_rpm: Sequence[float] = field(default_factory=_motor_rpm_factory)
    internal_temp_c: float = 0.0
    gps_satellite_count: int = 0
    gps_hdop: float = 0.0


@_dds_type(member_annotations=_CMD_ANN)
class DroneCommand:
    drone_id: int = 0
    timestamp_ns: int = 0
    command: int = 0
    target_position: GeoPoint = field(default_factory=GeoPoint)
    parameter: float = 0.0
    command_seq: int = 0
    issuer: str = ""


@_dds_type(member_annotations=_ALERT_ANN)
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


@_dds_type(member_annotations=_MISSION_ANN)
class MissionPlan:
    drone_id: int = 0
    timestamp_ns: int = 0
    waypoint_count: int = 0
    waypoints: Sequence[GeoPoint] = field(default_factory=list)
    cruise_speed_mps: float = 0.0
    cruise_altitude_m: float = 0.0
    is_active: bool = False
    mission_name: str = ""


@_dds_type
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
