"""Acceptance tests — SPEC section 7: each drone initializes with correct characteristics."""
import pytest

from drones.drone_config import DRONE_CONFIGS, get_config


# Expected personality table per SPEC section 7
EXPECTED = [
    {"id": 0, "callsign": "ALPHA",   "battery": 100.0, "speed": 10.0},
    {"id": 1, "callsign": "BRAVO",   "battery":  95.0, "speed": 12.0},
    {"id": 2, "callsign": "CHARLIE", "battery":  88.0, "speed": 10.0},
    {"id": 3, "callsign": "DELTA",   "battery": 100.0, "speed": 10.0},
    {"id": 4, "callsign": "ECHO",    "battery":  97.0, "speed": 10.0},
    {"id": 5, "callsign": "FOXTROT", "battery": 100.0, "speed":  8.0},
    {"id": 6, "callsign": "GOLF",    "battery":  92.0, "speed": 13.0},
    {"id": 7, "callsign": "HOTEL",   "battery": 100.0, "speed": 10.0},
]


class TestSpec07Personalities:
    """SPEC 7 — drone personality initialization."""

    @pytest.mark.parametrize("expected", EXPECTED, ids=[e["callsign"] for e in EXPECTED])
    def test_drone_characteristics(self, expected):
        cfg = get_config(expected["id"])
        assert cfg.callsign == expected["callsign"]
        assert cfg.start_battery == expected["battery"]
        assert cfg.cruise_speed == expected["speed"]
        # Every drone must have all four fault-multiplier keys
        for key in ("motor", "gps", "comm", "critical"):
            assert key in cfg.fault_multipliers

    def test_hotel_no_special_faults_and_full_battery(self):
        hotel = get_config(7)
        assert hotel.callsign == "HOTEL"
        assert hotel.start_battery == 100.0
        # All fault multipliers should be 1.0 (no special faults)
        for key, value in hotel.fault_multipliers.items():
            assert value == 1.0, f"HOTEL fault_multipliers[{key!r}] should be 1.0, got {value}"
