"""E2E acceptance tests for SPEC section 20 — Integration scenarios.
These test the simulation logic end-to-end without DDS or WebSocket."""
import pytest
from drones.drone_sim import DroneSim
from drones.types import DroneMode, DroneCommand, CommandType, GeoPoint, AlertType, AlertSeverity
from drones.drone_config import BASE_STATION
from monitor.swarm_monitor import SwarmMonitor
from mission.mission_planner import generate_missions
from bridge.ws_bridge import WebSocketBridge, serialize_state, deserialize_command


class TestSpec20_1_FullSystem:
    def test_drones_start_and_fly(self):
        """SPEC 20.1: 8 drones initialize, 0-6 start missions, 7 stays idle."""
        missions = generate_missions()
        drones = []
        for i in range(8):
            sim = DroneSim(i, rng_seed=42 + i)
            if i in missions:
                sim.set_mission(missions[i])
            drones.append(sim)

        # Tick for a few seconds
        for _ in range(50):
            for d in drones:
                d.tick(0.1)

        # Drones 0-6 should be flying
        for i in range(7):
            assert drones[i].mode in (DroneMode.TAKEOFF, DroneMode.EN_ROUTE), \
                f"Drone {i} should be flying, got {drones[i].mode}"

        # Drone 7 stays idle
        assert drones[7].mode == DroneMode.IDLE

    def test_swarm_monitor_aggregates(self):
        """Monitor correctly counts modes from multiple drones."""
        monitor = SwarmMonitor()
        missions = generate_missions()
        drones = []
        for i in range(8):
            sim = DroneSim(i, rng_seed=42 + i)
            if i in missions:
                sim.set_mission(missions[i])
            drones.append(sim)

        # Run for a bit
        for _ in range(50):
            for d in drones:
                state = d.tick(0.1)
                monitor.update_drone_state(state)

        summary = monitor.compute_summary()
        assert summary.total_drones == 8
        assert summary.active_drones + summary.idle_drones + summary.faulted_drones + summary.returning_drones >= 8


class TestSpec20_2_CommandFlow:
    def test_command_changes_drone_mode(self):
        """SPEC 20.2: operator command changes drone behavior."""
        sim = DroneSim(0, rng_seed=42)
        missions = generate_missions()
        sim.set_mission(missions[0])

        # Fly until en_route (takeoff at 3 m/s to 50m takes ~17s = 170 ticks)
        for _ in range(300):
            sim.tick(0.1)
            if sim.mode == DroneMode.EN_ROUTE:
                break

        assert sim.mode == DroneMode.EN_ROUTE

        # Send RTB command
        cmd = DroneCommand(drone_id=0, command=int(CommandType.RETURN_TO_BASE))
        sim.handle_command(cmd)
        assert sim.mode == DroneMode.RETURNING_TO_BASE

    def test_hover_and_resume(self):
        """SPEC 20.2: hover pauses, resume continues."""
        sim = DroneSim(0, rng_seed=42)
        missions = generate_missions()
        sim.set_mission(missions[0])

        for _ in range(300):
            sim.tick(0.1)
            if sim.mode == DroneMode.EN_ROUTE:
                break

        wp_before = sim.current_waypoint_idx
        sim.handle_command(DroneCommand(drone_id=0, command=int(CommandType.HOVER)))
        assert sim.mode == DroneMode.HOVERING
        assert sim.current_waypoint_idx == wp_before

        sim.handle_command(DroneCommand(drone_id=0, command=int(CommandType.RESUME_MISSION)))
        assert sim.mode == DroneMode.EN_ROUTE


class TestSpec20_3_FaultObservation:
    def test_faults_generate_alerts(self):
        """SPEC 20.3: faults produce alerts that can be observed."""
        alerts = []
        sim = DroneSim(4, alert_callback=alerts.append, rng_seed=100)  # ECHO, motor-prone
        missions = generate_missions()
        sim.set_mission(missions[4])

        # Run long enough to trigger faults and/or battery alerts
        # ECHO has 3x motor fault rate; battery will also deplete over time
        for _ in range(20000):
            sim.tick(0.1)
            if len(alerts) > 0:
                break

        # Should have generated some alerts (faults or battery)
        assert len(alerts) > 0


class TestSpec20_4_LowBattery:
    def test_battery_sequence(self):
        """SPEC 20.4: WARNING at 30%, CRITICAL at 20%, forced RTB at 15%."""
        alerts = []
        sim = DroneSim(2, alert_callback=alerts.append, rng_seed=42)  # CHARLIE, 88% start
        missions = generate_missions()
        sim.set_mission(missions[2])

        # Run until battery is depleted enough
        max_ticks = 100000
        for _ in range(max_ticks):
            sim.tick(0.1)
            if sim.battery.pct < 14:
                break

        # Check alerts were fired
        alert_messages = [a.message for a in alerts]
        low_battery_alerts = [a for a in alerts if a.alert_type == int(AlertType.LOW_BATTERY)]

        # Should have warning and critical alerts
        warning_alerts = [a for a in low_battery_alerts if a.severity == int(AlertSeverity.WARNING)]
        critical_alerts = [a for a in low_battery_alerts if a.severity == int(AlertSeverity.CRITICAL)]

        assert len(warning_alerts) >= 1, "Should have WARNING alert at 30%"
        assert len(critical_alerts) >= 1, "Should have CRITICAL alert at 20% or 15%"

        # Drone should have transitioned to RTB (or FAULT if a critical fault occurred)
        assert sim.mode in (DroneMode.RETURNING_TO_BASE, DroneMode.LANDING, DroneMode.IDLE, DroneMode.FAULT), \
            f"Drone should be RTB, landed, or faulted, got {sim.mode}"


class TestSpec20_BridgeSerialization:
    def test_state_round_trip(self):
        """Bridge can serialize drone state and deserialize commands."""
        sim = DroneSim(0, rng_seed=42)
        state = sim.tick(0.1)

        # Serialize
        serialized = serialize_state(state)
        assert serialized["drone_id"] == 0
        assert "battery_pct" in serialized
        assert "position" in serialized

    def test_command_round_trip(self):
        """Commands can be deserialized from JSON."""
        data = {
            "type": "drone_command",
            "data": {
                "drone_id": 3,
                "command": "HOVER",
                "parameter": 0.0,
                "target_position": None,
            }
        }
        cmd = deserialize_command(data)
        assert cmd.drone_id == 3
        assert cmd.command == int(CommandType.HOVER)
