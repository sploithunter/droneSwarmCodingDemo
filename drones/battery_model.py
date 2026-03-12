"""Battery simulation model for drone."""


class BatteryModel:
    """Simulates battery drain, voltage, and alert thresholds."""

    # Drain rates in percent per minute
    HOVER_DRAIN = 0.5
    CRUISE_DRAIN = 1.0
    HIGH_SPEED_DRAIN = 1.5
    HIGH_SPEED_THRESHOLD = 12.0  # m/s

    # Voltage range
    VOLTAGE_MAX = 16.8  # at 100%
    VOLTAGE_MIN = 13.2  # at 0%

    # Alert thresholds
    WARNING_THRESHOLD = 30.0
    CRITICAL_THRESHOLD = 20.0
    FORCED_RTB_THRESHOLD = 15.0

    # Voltage sag under load (volts)
    LOAD_SAG = 0.3

    def __init__(self, start_pct=100.0):
        self.pct = start_pct
        self._warning_fired = False
        self._critical_fired = False
        self._rtb_fired = False

    @property
    def voltage(self):
        """Calculate voltage from battery percentage. Linear 16.8V (100%) to 13.2V (0%)."""
        return self.VOLTAGE_MIN + (self.VOLTAGE_MAX - self.VOLTAGE_MIN) * (self.pct / 100.0)

    def voltage_under_load(self, is_flying=True):
        """Voltage with load sag applied during flight."""
        v = self.voltage
        if is_flying:
            v -= self.LOAD_SAG
        return max(self.VOLTAGE_MIN, v)

    def update(self, dt, ground_speed=0.0, is_flying=True):
        """
        Update battery for one timestep.

        Args:
            dt: time step in seconds
            ground_speed: current ground speed in m/s
            is_flying: whether the drone is in flight

        Returns:
            list of (alert_type, severity, message) tuples for any triggered alerts.
            Also returns force_rtb flag.
            Returns: (alerts: list, force_rtb: bool)
        """
        alerts = []
        force_rtb = False

        if not is_flying:
            # No drain on ground
            return alerts, force_rtb

        # Determine drain rate based on speed
        if ground_speed > self.HIGH_SPEED_THRESHOLD:
            drain_per_min = self.HIGH_SPEED_DRAIN
        elif ground_speed > 0.5:
            drain_per_min = self.CRUISE_DRAIN
        else:
            drain_per_min = self.HOVER_DRAIN

        # Apply drain
        drain = drain_per_min * (dt / 60.0)
        self.pct = max(0.0, self.pct - drain)

        # Check thresholds (fire each alert only once)
        if self.pct <= self.WARNING_THRESHOLD and not self._warning_fired:
            self._warning_fired = True
            alerts.append(("LOW_BATTERY", "WARNING", f"Battery at {self.pct:.1f}%"))

        if self.pct <= self.CRITICAL_THRESHOLD and not self._critical_fired:
            self._critical_fired = True
            alerts.append(("LOW_BATTERY", "CRITICAL", f"Battery critical at {self.pct:.1f}%"))

        if self.pct <= self.FORCED_RTB_THRESHOLD and not self._rtb_fired:
            self._rtb_fired = True
            force_rtb = True
            alerts.append(("LOW_BATTERY", "CRITICAL", f"Battery at {self.pct:.1f}% - forced RTB"))

        return alerts, force_rtb
