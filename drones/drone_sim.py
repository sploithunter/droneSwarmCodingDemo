"""Drone simulator — full state machine orchestrating physics, battery, and faults."""
import time
import math
import random
from drones.types import (
    DroneState, DroneMode, DroneCommand, DroneAlert,
    CommandType, AlertType, AlertSeverity, GeoPoint, Vector3, MissionPlan
)
from drones.flight_physics import FlightPhysics, haversine_distance
from drones.battery_model import BatteryModel
from drones.fault_injector import FaultInjector
from drones.drone_config import get_config, BASE_STATION, ASCENT_RATE, DESCENT_RATE, MAX_SPEED, UPDATE_HZ


class DroneSim:
    """Full drone simulator with state machine."""

    def __init__(self, drone_id, writer_callback=None, alert_callback=None, rng_seed=None):
        """
        Args:
            drone_id: 0-7
            writer_callback: callable(DroneState) — called each tick to publish state
            alert_callback: callable(DroneAlert) — called when alerts are generated
            rng_seed: optional seed for deterministic testing
        """
        self.config = get_config(drone_id)
        self.drone_id = drone_id
        self.callsign = self.config.callsign

        # State
        self.mode = DroneMode.IDLE
        self.mission = None
        self.current_waypoint_idx = 0
        self.total_waypoints = 0
        self.alert_seq = 0

        # Sub-systems
        self.physics = FlightPhysics(BASE_STATION[0], BASE_STATION[1], altitude=0.0)
        self.battery = BatteryModel(start_pct=self.config.start_battery)
        self.fault_injector = FaultInjector(
            fault_multipliers=self.config.fault_multipliers,
            rng_seed=rng_seed
        )

        # Callbacks
        self.writer_callback = writer_callback or (lambda s: None)
        self.alert_callback = alert_callback or (lambda a: None)

        # Flight params
        self.cruise_speed = self.config.cruise_speed
        self.cruise_altitude = 50.0  # default, overridden by mission
        self.target_altitude = 0.0
        self.goto_target = None  # (lat, lon, alt) for GOTO_WAYPOINT

        # Temperature model
        self.temperature = 35.0

        # Motor RPM
        self.motor_rpms = [0.0, 0.0, 0.0, 0.0]

        # Signal / GPS
        self.signal_strength = -50.0
        self.gps_sat_count = 12
        self.gps_hdop = 0.9

        # Distance tracking
        self.total_distance = 0.0
        self._last_lat = BASE_STATION[0]
        self._last_lon = BASE_STATION[1]

        # RNG for noise
        self.rng = random.Random(rng_seed)

    def set_mission(self, mission):
        """Assign a mission to this drone."""
        self.mission = mission
        self.total_waypoints = mission.waypoint_count if mission else 0
        self.cruise_speed = mission.cruise_speed_mps if mission else self.config.cruise_speed
        self.cruise_altitude = mission.cruise_altitude_m if mission else 50.0

        if mission and mission.is_active and self.mode == DroneMode.IDLE:
            self.mode = DroneMode.TAKEOFF
            self.target_altitude = self.cruise_altitude
            self.current_waypoint_idx = 0

    def handle_command(self, cmd):
        """Handle an incoming DroneCommand."""
        # Check if command is for us or broadcast
        if cmd.drone_id != self.drone_id and cmd.drone_id != 255:
            return

        ct = CommandType(cmd.command) if isinstance(cmd.command, int) else cmd.command

        if ct == CommandType.HOVER:
            if self.mode == DroneMode.EN_ROUTE:
                self.mode = DroneMode.HOVERING

        elif ct == CommandType.RESUME_MISSION:
            if self.mode == DroneMode.HOVERING:
                self.mode = DroneMode.EN_ROUTE

        elif ct == CommandType.RETURN_TO_BASE:
            if self.mode in (DroneMode.EN_ROUTE, DroneMode.HOVERING, DroneMode.FAULT):
                self.mode = DroneMode.RETURNING_TO_BASE
                self.goto_target = None

        elif ct == CommandType.EMERGENCY_LAND:
            if self.mode in (DroneMode.TAKEOFF, DroneMode.EN_ROUTE, DroneMode.HOVERING,
                           DroneMode.RETURNING_TO_BASE, DroneMode.FAULT):
                self.mode = DroneMode.LANDING
                self.goto_target = None

        elif ct == CommandType.GOTO_WAYPOINT:
            if self.mode in (DroneMode.EN_ROUTE, DroneMode.HOVERING):
                tp = cmd.target_position
                self.goto_target = (tp.latitude, tp.longitude, tp.altitude_m)
                self.mode = DroneMode.EN_ROUTE

        elif ct == CommandType.SET_SPEED:
            self.cruise_speed = min(cmd.parameter, MAX_SPEED)

        elif ct == CommandType.SET_ALTITUDE:
            self.cruise_altitude = cmd.parameter
            self.target_altitude = cmd.parameter

    def tick(self, dt):
        """
        Advance simulation by dt seconds. Returns DroneState.
        """
        is_flying = self.mode not in (DroneMode.IDLE, DroneMode.LANDED)

        # --- Fault injection (only while flying) ---
        if is_flying and self.mode != DroneMode.FAULT:
            new_faults = self.fault_injector.check_faults(dt)
            for fault_type, severity, message in new_faults:
                self._publish_alert(fault_type, severity, message)
                if fault_type == "CRITICAL_FAULT":
                    self.mode = DroneMode.FAULT

        # --- State machine ---
        if self.mode == DroneMode.IDLE:
            self._update_idle(dt)
        elif self.mode == DroneMode.TAKEOFF:
            self._update_takeoff(dt)
        elif self.mode == DroneMode.EN_ROUTE:
            self._update_en_route(dt)
        elif self.mode == DroneMode.HOVERING:
            self._update_hovering(dt)
        elif self.mode == DroneMode.RETURNING_TO_BASE:
            self._update_rtb(dt)
        elif self.mode == DroneMode.LANDING:
            self._update_landing(dt)
        elif self.mode == DroneMode.LANDED:
            self._update_landed(dt)
        elif self.mode == DroneMode.FAULT:
            self._update_fault(dt)

        # --- Battery ---
        alerts, force_rtb = self.battery.update(dt, self.physics.ground_speed, is_flying)
        for alert_type_str, severity_str, message in alerts:
            self._publish_alert(alert_type_str, severity_str, message)

        if force_rtb and self.mode in (DroneMode.EN_ROUTE, DroneMode.HOVERING):
            self.mode = DroneMode.RETURNING_TO_BASE

        # --- Temperature ---
        if is_flying:
            self.temperature = min(65.0, self.temperature + 0.5 * (dt / 60.0))
        else:
            self.temperature = max(20.0, self.temperature - 1.0 * (dt / 60.0))

        # --- Motor RPMs ---
        self._update_motor_rpms()

        # --- GPS ---
        reported_lat, reported_lon = self.physics.lat, self.physics.lon
        sat_count, hdop = self.gps_sat_count, self.gps_hdop
        if is_flying:
            sat_count = 12
            hdop = 0.9
        reported_lat, reported_lon, sat_count, hdop = self.fault_injector.apply_gps_effect(
            reported_lat, reported_lon, sat_count, hdop
        )

        # --- Distance tracking ---
        dist = haversine_distance(self._last_lat, self._last_lon, self.physics.lat, self.physics.lon)
        self.total_distance += dist
        self._last_lat = self.physics.lat
        self._last_lon = self.physics.lon

        # --- Signal strength ---
        base_dist = haversine_distance(self.physics.lat, self.physics.lon, BASE_STATION[0], BASE_STATION[1])
        self.signal_strength = -50.0 - (base_dist / 100.0)  # degrades with distance

        # --- Build state ---
        progress = 0.0
        if self.total_waypoints > 0:
            progress = (self.current_waypoint_idx / self.total_waypoints) * 100.0

        state = DroneState(
            drone_id=self.drone_id,
            timestamp_ns=int(time.time() * 1e9),
            position=GeoPoint(
                latitude=reported_lat,
                longitude=reported_lon,
                altitude_m=self.physics.altitude
            ),
            heading_deg=self.physics.heading,
            velocity=Vector3(
                x=self.physics.vx,
                y=self.physics.vy,
                z=self.physics.vz
            ),
            ground_speed_mps=self.physics.ground_speed,
            mode=int(self.mode),
            battery_pct=self.battery.pct,
            battery_voltage=self.battery.voltage_under_load(is_flying),
            signal_strength_dbm=self.signal_strength,
            current_waypoint_idx=self.current_waypoint_idx,
            total_waypoints=self.total_waypoints,
            mission_progress_pct=progress,
            motor_rpm=self.motor_rpms,
            internal_temp_c=self.temperature,
            gps_satellite_count=sat_count,
            gps_hdop=hdop,
        )

        # Publish (skip if comm silent)
        if not self.fault_injector.is_comm_silent():
            self.writer_callback(state)

        return state

    # --- State handlers ---

    def _update_idle(self, dt):
        self.physics.speed = 0.0
        self.physics.altitude = 0.0
        self.physics.vertical_speed = 0.0

    def _update_takeoff(self, dt):
        self.target_altitude = self.cruise_altitude
        self.physics.update(dt, target_altitude=self.target_altitude)
        if self.physics.altitude >= self.target_altitude - 0.5:
            self.mode = DroneMode.EN_ROUTE

    def _update_en_route(self, dt):
        target_wp = self._get_target_waypoint()
        if target_wp is None:
            self.mode = DroneMode.HOVERING
            return

        target_lat, target_lon = target_wp
        self.target_altitude = self._get_target_altitude()

        reached, dist = self.physics.update(
            dt,
            target_waypoint=(target_lat, target_lon),
            target_altitude=self.target_altitude,
            cruise_speed=self.cruise_speed
        )

        if reached:
            self.current_waypoint_idx += 1
            if self.current_waypoint_idx >= self.total_waypoints:
                # Mission complete — loop back
                self.current_waypoint_idx = 0
                self._publish_alert("MISSION_COMPLETE", "INFO",
                    f"{self.callsign} completed mission loop")

    def _update_hovering(self, dt):
        self.physics.update(dt, target_altitude=self.target_altitude)

    def _update_rtb(self, dt):
        dist = haversine_distance(
            self.physics.lat, self.physics.lon,
            BASE_STATION[0], BASE_STATION[1]
        )

        if dist <= 10.0:
            self.mode = DroneMode.LANDING
            return

        self.physics.update(
            dt,
            target_waypoint=(BASE_STATION[0], BASE_STATION[1]),
            target_altitude=self.cruise_altitude,
            cruise_speed=self.cruise_speed
        )

    def _update_landing(self, dt):
        self.target_altitude = 0.0
        self.physics.update(dt, target_altitude=0.0)
        if self.physics.altitude < 0.5:
            self.physics.altitude = 0.0
            self.physics.speed = 0.0
            self.physics.vertical_speed = 0.0
            # Transition through LANDED to IDLE in the same tick
            self.mode = DroneMode.IDLE

    def _update_landed(self, dt):
        self.physics.speed = 0.0
        self.physics.altitude = 0.0
        self.physics.vertical_speed = 0.0
        self.mode = DroneMode.IDLE

    def _update_fault(self, dt):
        # Hover in place
        self.physics.update(dt, target_altitude=self.physics.altitude)

    # --- Helpers ---

    def _get_target_waypoint(self):
        """Get current target waypoint as (lat, lon) or None."""
        if self.goto_target is not None:
            return (self.goto_target[0], self.goto_target[1])
        if self.mission and self.current_waypoint_idx < len(self.mission.waypoints):
            wp = self.mission.waypoints[self.current_waypoint_idx]
            return (wp.latitude, wp.longitude)
        return None

    def _get_target_altitude(self):
        """Get target altitude for current waypoint."""
        if self.goto_target is not None:
            return self.goto_target[2]
        if self.mission and self.current_waypoint_idx < len(self.mission.waypoints):
            return self.mission.waypoints[self.current_waypoint_idx].altitude_m
        return self.cruise_altitude

    def _update_motor_rpms(self):
        """Update motor RPMs based on current flight mode."""
        if self.mode in (DroneMode.IDLE, DroneMode.LANDED):
            self.motor_rpms = [0.0, 0.0, 0.0, 0.0]
            return

        # Base RPM by mode
        if self.mode == DroneMode.TAKEOFF:
            base = self.rng.uniform(6000, 7000)
        elif self.mode == DroneMode.LANDING:
            base = self.rng.uniform(3500, 4500)
        elif self.mode == DroneMode.HOVERING or self.mode == DroneMode.FAULT:
            base = self.rng.uniform(4500, 5000)
        else:
            # EN_ROUTE or RTB — proportional to speed
            speed_ratio = self.physics.ground_speed / MAX_SPEED if MAX_SPEED > 0 else 0
            base = 5000 + speed_ratio * 1000  # 5000-6000

        # Add Gaussian noise ±100 RPM
        self.motor_rpms = [
            max(0, base + self.rng.gauss(0, 100)) for _ in range(4)
        ]

        # Apply motor fault effects
        self.motor_rpms = self.fault_injector.apply_motor_effect(self.motor_rpms)

    def _publish_alert(self, alert_type_str, severity_str, message):
        """Create and publish a DroneAlert."""
        # Map string to enum
        alert_type_map = {
            "LOW_BATTERY": AlertType.LOW_BATTERY,
            "MOTOR_FAULT": AlertType.MOTOR_FAULT,
            "GPS_DEGRADED": AlertType.GPS_DEGRADED,
            "COMMUNICATION_TIMEOUT": AlertType.COMMUNICATION_TIMEOUT,
            "MISSION_COMPLETE": AlertType.MISSION_COMPLETE,
            "CRITICAL_FAULT": AlertType.MOTOR_FAULT,  # map to nearest
            "GEOFENCE_BREACH": AlertType.GEOFENCE_BREACH,
            "COLLISION_WARNING": AlertType.COLLISION_WARNING,
        }
        severity_map = {
            "INFO": AlertSeverity.INFO,
            "WARNING": AlertSeverity.WARNING,
            "CRITICAL": AlertSeverity.CRITICAL,
        }

        self.alert_seq += 1
        alert = DroneAlert(
            drone_id=self.drone_id,
            alert_seq=self.alert_seq,
            timestamp_ns=int(time.time() * 1e9),
            alert_type=int(alert_type_map.get(alert_type_str, AlertType.MOTOR_FAULT)),
            severity=int(severity_map.get(severity_str, AlertSeverity.WARNING)),
            message=message,
            position=GeoPoint(
                latitude=self.physics.lat,
                longitude=self.physics.lon,
                altitude_m=self.physics.altitude
            ),
            battery_pct=self.battery.pct,
            drone_mode=int(self.mode),
            acknowledged=False,
        )
        self.alert_callback(alert)
