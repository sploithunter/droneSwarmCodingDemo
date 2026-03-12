"""Unit tests for WebSocket bridge."""
import json
import time
import pytest
from bridge.ws_bridge import (
    serialize_state, serialize_alert, serialize_mission, serialize_summary,
    deserialize_command, WebSocketBridge, create_batch_message
)
from drones.types import (
    DroneState, DroneAlert, MissionPlan, SwarmSummary, DroneCommand,
    GeoPoint, Vector3, CommandType, DroneMode, AlertType, AlertSeverity
)


class TestSerialization:
    def test_serialize_state(self):
        state = DroneState(drone_id=3, battery_pct=85.0, mode=int(DroneMode.EN_ROUTE))
        d = serialize_state(state)
        assert d["drone_id"] == 3
        assert d["battery_pct"] == 85.0
        assert d["mode"] == int(DroneMode.EN_ROUTE)

    def test_serialize_alert(self):
        alert = DroneAlert(
            drone_id=2, alert_seq=5,
            alert_type=int(AlertType.LOW_BATTERY),
            severity=int(AlertSeverity.WARNING),
            message="Low battery"
        )
        d = serialize_alert(alert)
        assert d["drone_id"] == 2
        assert d["alert_seq"] == 5
        assert d["message"] == "Low battery"

    def test_serialize_mission(self):
        mission = MissionPlan(
            drone_id=1,
            waypoint_count=4,
            waypoints=[GeoPoint(37.386, -122.084, 50.0)],
            is_active=True,
            mission_name="Test"
        )
        d = serialize_mission(mission)
        assert d["drone_id"] == 1
        assert d["is_active"] == True
        assert len(d["waypoints"]) == 1

    def test_serialize_summary(self):
        summary = SwarmSummary(
            summary_id=0, total_drones=8,
            active_drones=5, avg_battery_pct=73.25
        )
        d = serialize_summary(summary)
        assert d["total_drones"] == 8
        assert d["active_drones"] == 5

    def test_serialize_state_is_json_safe(self):
        state = DroneState(drone_id=0, motor_rpm=[5000.0, 5100.0, 4900.0, 5050.0])
        d = serialize_state(state)
        json_str = json.dumps(d)
        parsed = json.loads(json_str)
        assert parsed["motor_rpm"] == [5000.0, 5100.0, 4900.0, 5050.0]


class TestDeserialization:
    def test_deserialize_command_string(self):
        data = {
            "type": "drone_command",
            "data": {
                "drone_id": 3,
                "command": "RETURN_TO_BASE",
                "parameter": 0.0
            }
        }
        cmd = deserialize_command(data)
        assert cmd.drone_id == 3
        assert cmd.command == int(CommandType.RETURN_TO_BASE)

    def test_deserialize_command_with_target(self):
        data = {
            "type": "drone_command",
            "data": {
                "drone_id": 0,
                "command": "GOTO_WAYPOINT",
                "target_position": {
                    "latitude": 37.388,
                    "longitude": -122.085,
                    "altitude_m": 60.0
                },
                "parameter": 0.0
            }
        }
        cmd = deserialize_command(data)
        assert cmd.command == int(CommandType.GOTO_WAYPOINT)
        assert abs(cmd.target_position.latitude - 37.388) < 0.001

    def test_deserialize_command_null_target(self):
        data = {
            "type": "drone_command",
            "data": {
                "drone_id": 1,
                "command": "HOVER",
                "target_position": None,
                "parameter": 0.0
            }
        }
        cmd = deserialize_command(data)
        assert cmd.command == int(CommandType.HOVER)

    def test_deserialize_set_speed(self):
        data = {
            "data": {
                "drone_id": 0,
                "command": "SET_SPEED",
                "parameter": 13.0
            }
        }
        cmd = deserialize_command(data)
        assert cmd.command == int(CommandType.SET_SPEED)
        assert cmd.parameter == 13.0


class TestBatching:
    def test_batch_message_structure(self):
        states = [
            DroneState(drone_id=i, battery_pct=80.0 + i)
            for i in range(8)
        ]
        batch = create_batch_message(states)
        assert batch["type"] == "drone_state_batch"
        assert "timestamp_ns" in batch
        assert len(batch["drones"]) == 8

    def test_bridge_buffers_states(self):
        bridge = WebSocketBridge()
        state = DroneState(drone_id=0, battery_pct=85.0)
        bridge.on_drone_state(state)
        assert 0 in bridge._state_buffer

    def test_bridge_latest_state_wins(self):
        bridge = WebSocketBridge()
        bridge.on_drone_state(DroneState(drone_id=0, battery_pct=85.0))
        bridge.on_drone_state(DroneState(drone_id=0, battery_pct=80.0))
        assert bridge._state_buffer[0]["battery_pct"] == 80.0

    def test_flush_clears_buffer(self):
        bridge = WebSocketBridge()
        bridge._last_batch_time = 0  # force flush
        bridge.on_drone_state(DroneState(drone_id=0))
        result = bridge.flush_batch()
        assert result is not None
        assert len(bridge._state_buffer) == 0

    def test_flush_returns_none_when_empty(self):
        bridge = WebSocketBridge()
        bridge._last_batch_time = 0
        result = bridge.flush_batch()
        assert result is None

    def test_flush_throttled(self):
        bridge = WebSocketBridge()
        bridge._last_batch_time = time.time()  # just flushed
        bridge.on_drone_state(DroneState(drone_id=0))
        result = bridge.flush_batch()
        assert result is None  # throttled

    def test_batch_json_parseable(self):
        bridge = WebSocketBridge()
        bridge._last_batch_time = 0
        for i in range(8):
            bridge.on_drone_state(DroneState(drone_id=i, battery_pct=90.0 - i))
        result = bridge.flush_batch()
        data = json.loads(result)
        assert data["type"] == "drone_state_batch"
        assert len(data["drones"]) == 8


class TestCommandRelay:
    def test_command_callback_called(self):
        received = []
        bridge = WebSocketBridge(command_callback=received.append)
        # Simulate what _handle_client does
        data = {
            "type": "drone_command",
            "data": {
                "drone_id": 3,
                "command": "RETURN_TO_BASE",
                "parameter": 0.0
            }
        }
        cmd = deserialize_command(data)
        bridge.command_callback(cmd)
        assert len(received) == 1
        assert received[0].drone_id == 3
