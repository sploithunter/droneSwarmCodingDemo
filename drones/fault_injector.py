"""Fault injection system for drone simulation."""
import random


class FaultInjector:
    """Probabilistic fault injection with personality multipliers."""

    # Base fault rates (probability per minute)
    BASE_RATES = {
        "motor": 0.02,      # 2% per minute
        "gps": 0.03,        # 3% per minute
        "comm": 0.01,       # 1% per minute
        "critical": 0.005,  # 0.5% per minute
    }

    # Duration ranges in seconds
    DURATION_RANGES = {
        "motor": (30, 60),
        "gps": (20, 40),
        "comm": (3, 5),
        "critical": None,  # indefinite
    }

    def __init__(self, fault_multipliers=None, rng_seed=None):
        """
        Args:
            fault_multipliers: dict mapping fault type to multiplier (e.g. {"gps": 3.0})
            rng_seed: optional seed for deterministic testing
        """
        self.multipliers = fault_multipliers or {"motor": 1.0, "gps": 1.0, "comm": 1.0, "critical": 1.0}
        self.rng = random.Random(rng_seed)

        # Active faults: type -> remaining duration (seconds)
        self.active_faults = {}

        # Fault effects
        self.motor_fault_idx = None  # which motor is affected
        self.motor_rpm_factor = 1.0  # RPM multiplier for affected motor
        self.gps_sat_count = None
        self.gps_hdop_override = None
        self.comm_silent = False

    def check_faults(self, dt):
        """
        Check for new faults and update active fault timers.

        Args:
            dt: time step in seconds

        Returns:
            list of (fault_type, severity, message) for newly triggered faults
        """
        new_faults = []

        # Update active fault timers
        expired = []
        for fault_type, remaining in self.active_faults.items():
            if remaining is not None:
                self.active_faults[fault_type] = remaining - dt
                if self.active_faults[fault_type] <= 0:
                    expired.append(fault_type)

        for fault_type in expired:
            self._clear_fault(fault_type)

        # Check for new faults (only if not already active)
        for fault_type, base_rate in self.BASE_RATES.items():
            if fault_type in self.active_faults:
                continue

            rate = base_rate * self.multipliers.get(fault_type, 1.0)
            # Convert per-minute probability to per-dt probability
            prob = rate * (dt / 60.0)

            if self.rng.random() < prob:
                fault = self._trigger_fault(fault_type)
                if fault:
                    new_faults.append(fault)

        return new_faults

    def _trigger_fault(self, fault_type):
        """Trigger a specific fault, return (fault_type, severity, message) or None."""
        duration_range = self.DURATION_RANGES[fault_type]
        duration = None
        if duration_range is not None:
            duration = self.rng.uniform(duration_range[0], duration_range[1])

        self.active_faults[fault_type] = duration

        if fault_type == "motor":
            self.motor_fault_idx = self.rng.randint(0, 3)
            self.motor_rpm_factor = self.rng.uniform(0.5, 0.7)  # 30-50% drop
            return ("MOTOR_FAULT", "WARNING", f"Motor {self.motor_fault_idx} RPM degraded")

        elif fault_type == "gps":
            self.gps_sat_count = self.rng.randint(3, 5)
            self.gps_hdop_override = self.rng.uniform(4.0, 8.0)
            return ("GPS_DEGRADED", "WARNING", f"GPS degraded: {self.gps_sat_count} sats, HDOP {self.gps_hdop_override:.1f}")

        elif fault_type == "comm":
            self.comm_silent = True
            return ("COMMUNICATION_TIMEOUT", "WARNING", "Communication timeout")

        elif fault_type == "critical":
            return ("CRITICAL_FAULT", "CRITICAL", "Critical system fault - hovering in place")

        return None

    def _clear_fault(self, fault_type):
        """Clear a fault and its effects."""
        del self.active_faults[fault_type]

        if fault_type == "motor":
            self.motor_fault_idx = None
            self.motor_rpm_factor = 1.0
        elif fault_type == "gps":
            self.gps_sat_count = None
            self.gps_hdop_override = None
        elif fault_type == "comm":
            self.comm_silent = False

    def apply_motor_effect(self, rpms):
        """Apply motor fault effects to RPM array. Returns modified copy."""
        result = list(rpms)
        if self.motor_fault_idx is not None and "motor" in self.active_faults:
            result[self.motor_fault_idx] *= self.motor_rpm_factor
        return result

    def apply_gps_effect(self, lat, lon, sat_count, hdop):
        """Apply GPS fault effects. Returns (lat, lon, sat_count, hdop)."""
        if "gps" in self.active_faults and self.gps_sat_count is not None:
            # Add random drift up to 2m
            drift_m = self.rng.uniform(0, 2.0)
            drift_angle = self.rng.uniform(0, 360)
            import math
            dlat = drift_m * math.cos(math.radians(drift_angle)) / 111320.0
            dlon = drift_m * math.sin(math.radians(drift_angle)) / (111320.0 * math.cos(math.radians(lat)))
            return (lat + dlat, lon + dlon, self.gps_sat_count, self.gps_hdop_override)
        return (lat, lon, sat_count, hdop)

    def has_critical_fault(self):
        """Check if a critical fault is active."""
        return "critical" in self.active_faults

    def is_comm_silent(self):
        """Check if communication is silenced."""
        return self.comm_silent and "comm" in self.active_faults
