"""Acceptance tests for SPEC section 1.1 and 1.2 -- DDS data types."""

import pytest
from drones.types import (
    DroneMode,
    AlertSeverity,
    AlertType,
    CommandType,
    GeoPoint,
    Vector3,
    DroneState,
    DroneCommand,
    DroneAlert,
    MissionPlan,
    SwarmSummary,
)


# ------------------------------------------------------------------
# SPEC 1.1 -- All 7 types are importable and instantiable
# ------------------------------------------------------------------

class TestSpec11TypesImportable:
    """All seven IDL-derived types can be imported and instantiated."""

    def test_geopoint_instantiable(self):
        obj = GeoPoint()
        assert obj is not None

    def test_vector3_instantiable(self):
        obj = Vector3()
        assert obj is not None

    def test_drone_state_instantiable(self):
        obj = DroneState()
        assert obj is not None

    def test_drone_command_instantiable(self):
        obj = DroneCommand()
        assert obj is not None

    def test_drone_alert_instantiable(self):
        obj = DroneAlert()
        assert obj is not None

    def test_mission_plan_instantiable(self):
        obj = MissionPlan()
        assert obj is not None

    def test_swarm_summary_instantiable(self):
        obj = SwarmSummary()
        assert obj is not None


# ------------------------------------------------------------------
# SPEC 1.2 -- Enum values match IDL exactly
# ------------------------------------------------------------------

class TestSpec12EnumValues:
    """Enum members and their integer values match the IDL definition."""

    # DroneMode: 8 values in order
    def test_drone_mode_count(self):
        assert len(DroneMode) == 8

    def test_drone_mode_values(self):
        expected = [
            ("IDLE", 0),
            ("TAKEOFF", 1),
            ("EN_ROUTE", 2),
            ("HOVERING", 3),
            ("RETURNING_TO_BASE", 4),
            ("LANDING", 5),
            ("LANDED", 6),
            ("FAULT", 7),
        ]
        for name, value in expected:
            assert DroneMode[name] == value

    # AlertSeverity: 3 values
    def test_alert_severity_count(self):
        assert len(AlertSeverity) == 3

    def test_alert_severity_values(self):
        expected = [("INFO", 0), ("WARNING", 1), ("CRITICAL", 2)]
        for name, value in expected:
            assert AlertSeverity[name] == value

    # AlertType: 7 values
    def test_alert_type_count(self):
        assert len(AlertType) == 7

    def test_alert_type_values(self):
        expected = [
            ("LOW_BATTERY", 0),
            ("GEOFENCE_BREACH", 1),
            ("COLLISION_WARNING", 2),
            ("MOTOR_FAULT", 3),
            ("GPS_DEGRADED", 4),
            ("COMMUNICATION_TIMEOUT", 5),
            ("MISSION_COMPLETE", 6),
        ]
        for name, value in expected:
            assert AlertType[name] == value

    # CommandType: 7 values
    def test_command_type_count(self):
        assert len(CommandType) == 7

    def test_command_type_values(self):
        expected = [
            ("GOTO_WAYPOINT", 0),
            ("RETURN_TO_BASE", 1),
            ("HOVER", 2),
            ("RESUME_MISSION", 3),
            ("EMERGENCY_LAND", 4),
            ("SET_SPEED", 5),
            ("SET_ALTITUDE", 6),
        ]
        for name, value in expected:
            assert CommandType[name] == value


# ------------------------------------------------------------------
# DroneState motor_rpm field
# ------------------------------------------------------------------

class TestSpec12MotorRpm:
    """DroneState.motor_rpm is a list of length 4."""

    def test_motor_rpm_is_list(self):
        s = DroneState()
        assert hasattr(s.motor_rpm, '__len__')  # list or DDS Sequence

    def test_motor_rpm_length(self):
        s = DroneState()
        assert len(s.motor_rpm) == 4
