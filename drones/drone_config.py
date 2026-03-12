"""Drone configuration table — per-drone personalities and physics constants."""
from dataclasses import dataclass, field


@dataclass
class DroneConfig:
    drone_id: int
    callsign: str
    start_battery: float
    cruise_speed: float
    fault_multipliers: dict = field(default_factory=dict)


# 8 drone configs per VISION.md section 4.5
DRONE_CONFIGS = [
    DroneConfig(0, "ALPHA", 100.0, 10.0, {"motor": 1.0, "gps": 1.0, "comm": 1.0, "critical": 1.0}),
    DroneConfig(1, "BRAVO", 95.0, 12.0, {"motor": 1.0, "gps": 1.0, "comm": 1.0, "critical": 1.0}),
    DroneConfig(2, "CHARLIE", 88.0, 10.0, {"motor": 1.0, "gps": 1.0, "comm": 1.0, "critical": 1.0}),
    DroneConfig(3, "DELTA", 100.0, 10.0, {"motor": 1.0, "gps": 3.0, "comm": 1.0, "critical": 1.0}),
    DroneConfig(4, "ECHO", 97.0, 10.0, {"motor": 3.0, "gps": 1.0, "comm": 1.0, "critical": 1.0}),
    DroneConfig(5, "FOXTROT", 100.0, 8.0, {"motor": 1.0, "gps": 1.0, "comm": 1.0, "critical": 1.0}),
    DroneConfig(6, "GOLF", 92.0, 13.0, {"motor": 1.0, "gps": 1.0, "comm": 1.0, "critical": 1.0}),
    DroneConfig(7, "HOTEL", 100.0, 10.0, {"motor": 1.0, "gps": 1.0, "comm": 1.0, "critical": 1.0}),
]

# Base station and operational area
BASE_STATION = (37.3861, -122.0839)  # lat, lon
OPERATIONAL_AREA = {
    "center": BASE_STATION,
    "width_m": 2000,
    "height_m": 2000,
}

# Physics constants
MAX_SPEED = 15.0        # m/s
ASCENT_RATE = 3.0       # m/s
DESCENT_RATE = 2.0      # m/s
TURN_RATE = 45.0        # deg/s
ACCELERATION = 3.0      # m/s^2
UPDATE_HZ = 10          # ticks per second
MAX_ALTITUDE = 120.0    # meters AGL


def get_config(drone_id: int) -> DroneConfig:
    """Get config for a drone by ID."""
    if 0 <= drone_id < len(DRONE_CONFIGS):
        return DRONE_CONFIGS[drone_id]
    raise ValueError(f"Invalid drone_id: {drone_id}")
