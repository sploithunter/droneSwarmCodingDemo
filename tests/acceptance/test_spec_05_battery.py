"""Acceptance tests for SPEC 5 - Battery Model."""

import pytest
from drones.battery_model import BatteryModel


class TestSpec5_1_DrainRates:
    """SPEC 5.1: drain rates match (hover 0.5/min, cruise 1.0/min, high-speed 1.5/min)."""

    def test_hover_drain_rate(self):
        batt = BatteryModel(start_pct=100.0)
        batt.update(dt=60.0, ground_speed=0.0, is_flying=True)
        drain = 100.0 - batt.pct
        assert drain == pytest.approx(0.5, abs=0.01)

    def test_cruise_drain_rate(self):
        batt = BatteryModel(start_pct=100.0)
        batt.update(dt=60.0, ground_speed=10.0, is_flying=True)
        drain = 100.0 - batt.pct
        assert drain == pytest.approx(1.0, abs=0.01)

    def test_high_speed_drain_rate(self):
        batt = BatteryModel(start_pct=100.0)
        batt.update(dt=60.0, ground_speed=13.0, is_flying=True)
        drain = 100.0 - batt.pct
        assert drain == pytest.approx(1.5, abs=0.01)


class TestSpec5_2_VoltageCorrelation:
    """SPEC 5.2: voltage correlates (16.8V at 100%, 15.0V at 50%, 13.2V at 0%)."""

    def test_voltage_at_full(self):
        batt = BatteryModel(start_pct=100.0)
        assert batt.voltage == pytest.approx(16.8, abs=0.01)

    def test_voltage_at_half(self):
        batt = BatteryModel(start_pct=50.0)
        assert batt.voltage == pytest.approx(15.0, abs=0.01)

    def test_voltage_at_empty(self):
        batt = BatteryModel(start_pct=0.0)
        assert batt.voltage == pytest.approx(13.2, abs=0.01)


class TestSpec5_3_Alerts:
    """SPEC 5.3: WARNING at 30%, CRITICAL at 20%, forced RTB at 15%."""

    def test_warning_at_30(self):
        batt = BatteryModel(start_pct=30.5)
        alerts, force_rtb = batt.update(dt=60.0, ground_speed=0.0, is_flying=True)
        assert any(a[1] == "WARNING" for a in alerts)
        assert not force_rtb

    def test_critical_at_20(self):
        batt = BatteryModel(start_pct=20.5)
        batt._warning_fired = True
        alerts, force_rtb = batt.update(dt=60.0, ground_speed=0.0, is_flying=True)
        assert any(a[1] == "CRITICAL" for a in alerts)

    def test_forced_rtb_at_15(self):
        batt = BatteryModel(start_pct=15.5)
        batt._warning_fired = True
        batt._critical_fired = True
        alerts, force_rtb = batt.update(dt=60.0, ground_speed=0.0, is_flying=True)
        assert force_rtb is True
        assert any("forced RTB" in a[2] for a in alerts)
