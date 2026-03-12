"""Unit tests for drone configuration table."""
import pytest

from drones.drone_config import (
    DRONE_CONFIGS,
    BASE_STATION,
    MAX_SPEED,
    ASCENT_RATE,
    DESCENT_RATE,
    TURN_RATE,
    ACCELERATION,
    UPDATE_HZ,
    MAX_ALTITUDE,
    get_config,
)


class TestDroneConfigs:
    """Tests for the DRONE_CONFIGS list."""

    def test_exactly_8_configs(self):
        assert len(DRONE_CONFIGS) == 8

    def test_callsigns(self):
        expected = ["ALPHA", "BRAVO", "CHARLIE", "DELTA", "ECHO", "FOXTROT", "GOLF", "HOTEL"]
        assert [c.callsign for c in DRONE_CONFIGS] == expected

    def test_start_batteries(self):
        expected = [100.0, 95.0, 88.0, 100.0, 97.0, 100.0, 92.0, 100.0]
        assert [c.start_battery for c in DRONE_CONFIGS] == expected

    def test_cruise_speeds(self):
        expected = [10.0, 12.0, 10.0, 10.0, 10.0, 8.0, 13.0, 10.0]
        assert [c.cruise_speed for c in DRONE_CONFIGS] == expected

    def test_delta_gps_fault_multiplier(self):
        delta = DRONE_CONFIGS[3]
        assert delta.callsign == "DELTA"
        assert delta.fault_multipliers["gps"] == 3.0

    def test_echo_motor_fault_multiplier(self):
        echo = DRONE_CONFIGS[4]
        assert echo.callsign == "ECHO"
        assert echo.fault_multipliers["motor"] == 3.0


class TestGetConfig:
    """Tests for get_config helper."""

    @pytest.mark.parametrize("drone_id", range(8))
    def test_returns_correct_config(self, drone_id):
        cfg = get_config(drone_id)
        assert cfg.drone_id == drone_id
        assert cfg is DRONE_CONFIGS[drone_id]

    @pytest.mark.parametrize("bad_id", [8, -1])
    def test_raises_for_invalid_id(self, bad_id):
        with pytest.raises(ValueError, match="Invalid drone_id"):
            get_config(bad_id)


class TestBaseStation:
    """Tests for BASE_STATION coordinates."""

    def test_base_station(self):
        assert BASE_STATION == (37.3861, -122.0839)


class TestPhysicsConstants:
    """Tests for physics constants."""

    def test_max_speed(self):
        assert MAX_SPEED == 15.0

    def test_ascent_rate(self):
        assert ASCENT_RATE == 3.0

    def test_descent_rate(self):
        assert DESCENT_RATE == 2.0

    def test_turn_rate(self):
        assert TURN_RATE == 45.0

    def test_acceleration(self):
        assert ACCELERATION == 3.0

    def test_update_hz(self):
        assert UPDATE_HZ == 10

    def test_max_altitude(self):
        assert MAX_ALTITUDE == 120.0
