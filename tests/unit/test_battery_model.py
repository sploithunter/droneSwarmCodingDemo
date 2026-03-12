"""Unit tests for BatteryModel."""

import pytest
from drones.battery_model import BatteryModel


class TestBatteryDrainRates:
    def test_hover_drain_rate(self):
        """1 minute at hover drains ~0.5%."""
        batt = BatteryModel(start_pct=100.0)
        batt.update(dt=60.0, ground_speed=0.0, is_flying=True)
        assert batt.pct == pytest.approx(99.5, abs=0.01)

    def test_cruise_drain_rate(self):
        """1 minute at 10 m/s drains ~1.0%."""
        batt = BatteryModel(start_pct=100.0)
        batt.update(dt=60.0, ground_speed=10.0, is_flying=True)
        assert batt.pct == pytest.approx(99.0, abs=0.01)

    def test_high_speed_drain_rate(self):
        """1 minute at 13 m/s drains ~1.5%."""
        batt = BatteryModel(start_pct=100.0)
        batt.update(dt=60.0, ground_speed=13.0, is_flying=True)
        assert batt.pct == pytest.approx(98.5, abs=0.01)

    def test_no_drain_on_ground(self):
        """No drain when is_flying=False."""
        batt = BatteryModel(start_pct=50.0)
        batt.update(dt=600.0, ground_speed=0.0, is_flying=False)
        assert batt.pct == 50.0


class TestVoltage:
    def test_voltage_at_100_pct(self):
        """~16.8V at 100%."""
        batt = BatteryModel(start_pct=100.0)
        assert batt.voltage == pytest.approx(16.8, abs=0.01)

    def test_voltage_at_50_pct(self):
        """~15.0V at 50%."""
        batt = BatteryModel(start_pct=50.0)
        assert batt.voltage == pytest.approx(15.0, abs=0.01)

    def test_voltage_at_0_pct(self):
        """~13.2V at 0%."""
        batt = BatteryModel(start_pct=0.0)
        assert batt.voltage == pytest.approx(13.2, abs=0.01)

    def test_voltage_under_load_sag(self):
        """Flying voltage is lower than resting voltage."""
        batt = BatteryModel(start_pct=80.0)
        resting = batt.voltage
        loaded = batt.voltage_under_load(is_flying=True)
        assert loaded < resting
        assert loaded == pytest.approx(resting - BatteryModel.LOAD_SAG, abs=0.01)


class TestAlerts:
    def test_warning_at_30_pct(self):
        """Fires WARNING alert when crossing 30%."""
        batt = BatteryModel(start_pct=30.5)
        # Hover for 1 minute: drains 0.5% -> 30.0%
        alerts, force_rtb = batt.update(dt=60.0, ground_speed=0.0, is_flying=True)
        assert len(alerts) == 1
        assert alerts[0][0] == "LOW_BATTERY"
        assert alerts[0][1] == "WARNING"
        assert not force_rtb

    def test_critical_at_20_pct(self):
        """Fires CRITICAL alert when crossing 20%."""
        batt = BatteryModel(start_pct=20.5)
        batt._warning_fired = True  # already fired
        alerts, force_rtb = batt.update(dt=60.0, ground_speed=0.0, is_flying=True)
        assert any(a[1] == "CRITICAL" for a in alerts)
        assert not force_rtb

    def test_forced_rtb_at_15_pct(self):
        """Fires CRITICAL alert and force_rtb=True when crossing 15%."""
        batt = BatteryModel(start_pct=15.5)
        batt._warning_fired = True
        batt._critical_fired = True
        alerts, force_rtb = batt.update(dt=60.0, ground_speed=0.0, is_flying=True)
        assert force_rtb is True
        assert any("forced RTB" in a[2] for a in alerts)

    def test_alerts_fire_once(self):
        """Warning doesn't re-fire on subsequent updates."""
        batt = BatteryModel(start_pct=30.5)
        alerts1, _ = batt.update(dt=60.0, ground_speed=0.0, is_flying=True)
        assert len([a for a in alerts1 if a[1] == "WARNING"]) == 1
        # Second update should not re-fire warning
        alerts2, _ = batt.update(dt=60.0, ground_speed=0.0, is_flying=True)
        assert len([a for a in alerts2 if a[1] == "WARNING"]) == 0

    def test_battery_never_negative(self):
        """pct stays >= 0 even after extended drain."""
        batt = BatteryModel(start_pct=1.0)
        for _ in range(100):
            batt.update(dt=60.0, ground_speed=15.0, is_flying=True)
        assert batt.pct >= 0.0
