"""Acceptance tests for SPEC section 10 — WebSocket Bridge."""
import json
import time
import pytest
from bridge.ws_bridge import (
    WebSocketBridge, serialize_state, serialize_alert,
    deserialize_command, create_batch_message
)
from drones.types import (
    DroneState, DroneAlert, DroneCommand, MissionPlan, SwarmSummary,
    GeoPoint, CommandType, AlertType, AlertSeverity, DroneMode
)


class TestSpec10_2_DataForwarding:
    def test_batch_contains_all_drones(self):
        """SPEC 10.2: each batch contains state for all 8 drones."""
        states = [DroneState(drone_id=i) for i in range(8)]
        batch = create_batch_message(states)
        assert batch["type"] == "drone_state_batch"
        assert len(batch["drones"]) == 8
        ids = {d["drone_id"] for d in batch["drones"]}
        assert ids == set(range(8))

    def test_batch_structure(self):
        """SPEC 10.2: batch has type, timestamp_ns, drones fields."""
        batch = create_batch_message([DroneState(drone_id=0)])
        assert "type" in batch
        assert "timestamp_ns" in batch
        assert "drones" in batch
        assert isinstance(batch["timestamp_ns"], int)

    def test_alert_serialization(self):
        """SPEC 10.2: alert data contains all fields."""
        alert = DroneAlert(
            drone_id=2, alert_seq=5,
            alert_type=int(AlertType.LOW_BATTERY),
            severity=int(AlertSeverity.WARNING),
            message="Battery at 30%",
            battery_pct=30.0
        )
        d = serialize_alert(alert)
        assert d["drone_id"] == 2
        assert d["message"] == "Battery at 30%"
        json_str = json.dumps(d)
        assert json_str  # valid JSON


class TestSpec10_3_CommandRelay:
    def test_command_deserialization(self):
        """SPEC 10.3: dashboard command is deserialized correctly."""
        data = {
            "type": "drone_command",
            "data": {
                "drone_id": 3,
                "command": "RETURN_TO_BASE",
                "target_position": None,
                "parameter": 0.0
            }
        }
        cmd = deserialize_command(data)
        assert cmd.drone_id == 3
        assert cmd.command == int(CommandType.RETURN_TO_BASE)

    def test_goto_waypoint_command(self):
        """SPEC 10.3: GOTO_WAYPOINT with target_position."""
        data = {
            "type": "drone_command",
            "data": {
                "drone_id": 0,
                "command": "GOTO_WAYPOINT",
                "target_position": {"latitude": 37.388, "longitude": -122.085, "altitude_m": 60.0},
                "parameter": 0.0
            }
        }
        cmd = deserialize_command(data)
        assert cmd.command == int(CommandType.GOTO_WAYPOINT)
        assert abs(cmd.target_position.latitude - 37.388) < 0.001


class TestSpec10_Throttling:
    def test_5hz_throttle(self):
        """SPEC 10.2: bridge batches at 5Hz (200ms interval)."""
        bridge = WebSocketBridge()
        assert bridge._batch_interval == 0.2

    def test_states_buffered_not_immediate(self):
        """States are buffered, not sent immediately."""
        bridge = WebSocketBridge()
        bridge._last_batch_time = time.time()
        bridge.on_drone_state(DroneState(drone_id=0))
        # Flush should be throttled
        result = bridge.flush_batch()
        assert result is None
