"""Swarm monitor — aggregates drone states into SwarmSummary."""
import time
from drones.types import DroneState, DroneMode, SwarmSummary, DroneAlert
from drones.flight_physics import haversine_distance


class SwarmMonitor:
    """Computes aggregate swarm statistics from individual drone states."""

    def __init__(self, total_drones=8, writer_callback=None):
        self.total_drones = total_drones
        self.writer_callback = writer_callback or (lambda s: None)

        # Latest state per drone
        self.drone_states = {}

        # Distance tracking
        self._last_positions = {}  # drone_id -> (lat, lon)
        self.total_distance = 0.0

        # Alert tracking
        self.active_alerts = 0
        self.alert_counts = {}  # drone_id -> count of unacknowledged alerts

        # Mission tracking
        self.missions_completed = 0
        self._completed_missions = set()  # (drone_id, completion_count)

    def update_drone_state(self, state):
        """Process a new DroneState sample."""
        drone_id = state.drone_id

        # Track distance
        if drone_id in self._last_positions:
            last_lat, last_lon = self._last_positions[drone_id]
            dist = haversine_distance(
                last_lat, last_lon,
                state.position.latitude, state.position.longitude
            )
            self.total_distance += dist

        self._last_positions[drone_id] = (
            state.position.latitude, state.position.longitude
        )

        self.drone_states[drone_id] = state

    def update_alert(self, alert):
        """Process a new DroneAlert."""
        if not alert.acknowledged:
            self.alert_counts[alert.drone_id] = self.alert_counts.get(alert.drone_id, 0) + 1

    def record_mission_complete(self, drone_id):
        """Record a mission completion."""
        self.missions_completed += 1

    def compute_summary(self):
        """Compute and return a SwarmSummary from current state."""
        active = 0
        faulted = 0
        returning = 0
        idle = 0

        batteries = []
        min_battery = 100.0
        min_battery_drone = 0

        for drone_id, state in self.drone_states.items():
            mode = DroneMode(state.mode) if isinstance(state.mode, int) else state.mode

            if mode in (DroneMode.EN_ROUTE, DroneMode.HOVERING):
                active += 1
            elif mode == DroneMode.FAULT:
                faulted += 1
            elif mode == DroneMode.RETURNING_TO_BASE:
                returning += 1
            elif mode in (DroneMode.IDLE, DroneMode.LANDED):
                idle += 1
            # TAKEOFF and LANDING count as active
            elif mode in (DroneMode.TAKEOFF, DroneMode.LANDING):
                active += 1

            batteries.append(state.battery_pct)
            if state.battery_pct < min_battery:
                min_battery = state.battery_pct
                min_battery_drone = drone_id

        avg_battery = sum(batteries) / len(batteries) if batteries else 0.0
        total_alerts = sum(self.alert_counts.values())

        summary = SwarmSummary(
            summary_id=0,
            timestamp_ns=int(time.time() * 1e9),
            total_drones=len(self.drone_states),
            active_drones=active,
            faulted_drones=faulted,
            returning_drones=returning,
            idle_drones=idle,
            avg_battery_pct=avg_battery,
            min_battery_pct=min_battery if batteries else 0.0,
            min_battery_drone_id=min_battery_drone,
            total_distance_covered_m=self.total_distance,
            active_alerts=total_alerts,
            missions_completed=self.missions_completed,
        )

        self.writer_callback(summary)
        return summary
