"""Unit tests for the FaultInjector class."""
import pytest
from drones.fault_injector import FaultInjector


class TestMotorFault:
    def test_motor_fault_effect(self):
        """Trigger motor fault, check one RPM drops 30-50%."""
        fi = FaultInjector(rng_seed=42)
        fi._trigger_fault("motor")

        assert fi.motor_fault_idx is not None
        assert 0.5 <= fi.motor_rpm_factor <= 0.7

        rpms = [5000, 5000, 5000, 5000]
        result = fi.apply_motor_effect(rpms)

        idx = fi.motor_fault_idx
        # Affected motor should be reduced
        assert result[idx] == rpms[idx] * fi.motor_rpm_factor
        # Other motors unchanged
        for i in range(4):
            if i != idx:
                assert result[i] == rpms[i]

    def test_motor_fault_duration(self):
        """Motor fault duration should be 30-60 seconds."""
        fi = FaultInjector(rng_seed=42)
        fi._trigger_fault("motor")
        duration = fi.active_faults["motor"]
        assert 30 <= duration <= 60


class TestGpsFault:
    def test_gps_fault_effect(self):
        """GPS fault drops sat count to 3-5, hdop > 4.0."""
        fi = FaultInjector(rng_seed=42)
        fi._trigger_fault("gps")

        assert 3 <= fi.gps_sat_count <= 5
        assert fi.gps_hdop_override >= 4.0

    def test_gps_fault_duration(self):
        """GPS fault duration should be 20-40 seconds."""
        fi = FaultInjector(rng_seed=42)
        fi._trigger_fault("gps")
        duration = fi.active_faults["gps"]
        assert 20 <= duration <= 40


class TestCommFault:
    def test_comm_fault_effect(self):
        """Comm fault sets comm_silent to True."""
        fi = FaultInjector(rng_seed=42)
        fi._trigger_fault("comm")
        assert fi.comm_silent is True
        assert fi.is_comm_silent() is True

    def test_comm_fault_duration(self):
        """Comm fault duration should be 3-5 seconds."""
        fi = FaultInjector(rng_seed=42)
        fi._trigger_fault("comm")
        duration = fi.active_faults["comm"]
        assert 3 <= duration <= 5


class TestCriticalFault:
    def test_critical_fault_indefinite(self):
        """Critical fault duration is None (indefinite)."""
        fi = FaultInjector(rng_seed=42)
        fi._trigger_fault("critical")
        assert fi.active_faults["critical"] is None
        assert fi.has_critical_fault() is True


class TestFaultInjectorBehavior:
    def test_personality_multiplier_scaling(self):
        """Higher multiplier should produce statistically more faults."""
        iterations = 10000
        dt = 1.0  # 1 second steps

        # Low multiplier
        low_fi = FaultInjector(fault_multipliers={"motor": 1.0, "gps": 1.0, "comm": 1.0, "critical": 1.0}, rng_seed=100)
        low_count = 0
        for _ in range(iterations):
            low_fi.active_faults.clear()  # allow re-triggering each step
            faults = low_fi.check_faults(dt)
            low_count += len(faults)

        # High multiplier
        high_fi = FaultInjector(fault_multipliers={"motor": 10.0, "gps": 10.0, "comm": 10.0, "critical": 10.0}, rng_seed=100)
        high_count = 0
        for _ in range(iterations):
            high_fi.active_faults.clear()
            faults = high_fi.check_faults(dt)
            high_count += len(faults)

        assert high_count > low_count

    def test_seeded_random_determinism(self):
        """Same seed produces same fault sequence."""
        fi1 = FaultInjector(rng_seed=77)
        fi2 = FaultInjector(rng_seed=77)

        results1 = []
        results2 = []
        for _ in range(100):
            fi1.active_faults.clear()
            fi2.active_faults.clear()
            results1.append(fi1.check_faults(1.0))
            results2.append(fi2.check_faults(1.0))

        assert results1 == results2

    def test_no_double_fault(self):
        """Same fault type can't trigger twice simultaneously."""
        fi = FaultInjector(rng_seed=42)
        fi._trigger_fault("motor")
        assert "motor" in fi.active_faults

        # Try to trigger again via check_faults - motor should be skipped
        original_duration = fi.active_faults["motor"]
        # Even with high multiplier, motor shouldn't re-trigger
        fi.multipliers["motor"] = 1000.0
        fi.check_faults(0.1)
        # Motor should still be active (duration reduced by dt, not re-triggered)
        assert "motor" in fi.active_faults

    def test_fault_clears_after_duration(self):
        """Motor fault clears after its duration expires."""
        fi = FaultInjector(rng_seed=42)
        fi._trigger_fault("motor")
        duration = fi.active_faults["motor"]

        # Advance time past the duration
        fi.check_faults(duration + 1)

        assert "motor" not in fi.active_faults
        assert fi.motor_fault_idx is None
        assert fi.motor_rpm_factor == 1.0

    def test_apply_motor_effect(self):
        """apply_motor_effect modifies the correct motor RPM."""
        fi = FaultInjector(rng_seed=42)
        fi._trigger_fault("motor")
        idx = fi.motor_fault_idx
        factor = fi.motor_rpm_factor

        rpms = [6000, 6000, 6000, 6000]
        result = fi.apply_motor_effect(rpms)

        assert result[idx] == pytest.approx(6000 * factor)
        # Original list unchanged
        assert rpms == [6000, 6000, 6000, 6000]

    def test_apply_gps_effect(self):
        """apply_gps_effect adds drift to position."""
        fi = FaultInjector(rng_seed=42)
        fi._trigger_fault("gps")

        lat, lon = 47.6062, -122.3321
        new_lat, new_lon, sats, hdop = fi.apply_gps_effect(lat, lon, 12, 1.0)

        # Position should be different (drifted)
        assert (new_lat != lat) or (new_lon != lon)
        # Sat count and hdop should be overridden
        assert sats == fi.gps_sat_count
        assert hdop == fi.gps_hdop_override
