"""Acceptance tests for SPEC 6: Fault Injection."""
import pytest
from drones.fault_injector import FaultInjector


class TestSpec06Faults:
    """SPEC 6: Fault injection acceptance tests."""

    def test_spec_6_1_motor_fault(self):
        """SPEC 6.1: Motor fault reduces one motor 30-50%, other three normal, clears 30-60s."""
        fi = FaultInjector(rng_seed=42)
        fi._trigger_fault("motor")

        # Duration in range
        duration = fi.active_faults["motor"]
        assert 30 <= duration <= 60, f"Motor fault duration {duration} not in [30, 60]"

        # RPM factor means 30-50% reduction (factor 0.5 to 0.7)
        assert 0.5 <= fi.motor_rpm_factor <= 0.7

        # Apply to RPMs
        rpms = [5000, 5000, 5000, 5000]
        result = fi.apply_motor_effect(rpms)
        idx = fi.motor_fault_idx

        # Affected motor reduced
        assert result[idx] < rpms[idx]
        assert result[idx] >= rpms[idx] * 0.5
        assert result[idx] <= rpms[idx] * 0.7

        # Other three normal
        for i in range(4):
            if i != idx:
                assert result[i] == rpms[i], f"Motor {i} should be unaffected"

        # Fault clears after duration
        fi.check_faults(duration + 1)
        assert "motor" not in fi.active_faults
        assert fi.motor_fault_idx is None
        assert fi.motor_rpm_factor == 1.0

    def test_spec_6_2_gps_degradation(self):
        """SPEC 6.2: GPS degradation drops sats to 3-5, hdop > 4.0, clears 20-40s."""
        fi = FaultInjector(rng_seed=42)
        fi._trigger_fault("gps")

        # Duration in range
        duration = fi.active_faults["gps"]
        assert 20 <= duration <= 40, f"GPS fault duration {duration} not in [20, 40]"

        # Sat count and HDOP
        assert 3 <= fi.gps_sat_count <= 5
        assert fi.gps_hdop_override > 4.0

        # Apply GPS effect
        lat, lon = 47.6062, -122.3321
        new_lat, new_lon, sats, hdop = fi.apply_gps_effect(lat, lon, 12, 1.0)
        assert sats == fi.gps_sat_count
        assert hdop == fi.gps_hdop_override
        assert hdop > 4.0

        # Fault clears after duration
        fi.check_faults(duration + 1)
        assert "gps" not in fi.active_faults
        assert fi.gps_sat_count is None
        assert fi.gps_hdop_override is None

    def test_spec_6_3_comm_timeout(self):
        """SPEC 6.3: Comm timeout silences publishing 3-5s."""
        fi = FaultInjector(rng_seed=42)
        fi._trigger_fault("comm")

        # Duration in range
        duration = fi.active_faults["comm"]
        assert 3 <= duration <= 5, f"Comm fault duration {duration} not in [3, 5]"

        # Communication silenced
        assert fi.comm_silent is True
        assert fi.is_comm_silent() is True

        # Fault clears after duration
        fi.check_faults(duration + 1)
        assert "comm" not in fi.active_faults
        assert fi.comm_silent is False
        assert fi.is_comm_silent() is False

    def test_spec_6_4_critical_fault(self):
        """SPEC 6.4: Critical fault enters FAULT mode, indefinite."""
        fi = FaultInjector(rng_seed=42)
        result = fi._trigger_fault("critical")

        # Returns critical fault tuple
        assert result[0] == "CRITICAL_FAULT"
        assert result[1] == "CRITICAL"

        # Duration is indefinite (None)
        assert fi.active_faults["critical"] is None
        assert fi.has_critical_fault() is True

        # Even after a long time, fault persists
        fi.check_faults(3600)  # 1 hour
        assert fi.has_critical_fault() is True
        assert "critical" in fi.active_faults
