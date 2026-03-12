"""Flight physics engine — kinematic model for drone simulation."""
import math
from dataclasses import dataclass, field
from drones.drone_config import MAX_SPEED, ASCENT_RATE, DESCENT_RATE, TURN_RATE, ACCELERATION, MAX_ALTITUDE


# Earth radius in meters
EARTH_RADIUS = 6371000.0
# Meters per degree latitude
METERS_PER_DEG_LAT = 111320.0


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in meters between two lat/lon points."""
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return 2 * EARTH_RADIUS * math.asin(math.sqrt(a))


def calculate_bearing(lat1, lon1, lat2, lon2):
    """Calculate bearing in degrees from point 1 to point 2. Returns 0-360."""
    dlon = math.radians(lon2 - lon1)
    lat1r = math.radians(lat1)
    lat2r = math.radians(lat2)
    x = math.sin(dlon) * math.cos(lat2r)
    y = math.cos(lat1r) * math.sin(lat2r) - math.sin(lat1r) * math.cos(lat2r) * math.cos(dlon)
    bearing = math.degrees(math.atan2(x, y))
    return bearing % 360


def normalize_angle(angle):
    """Normalize angle to 0-360 range."""
    return angle % 360


class FlightPhysics:
    """Kinematic flight model for a single drone."""

    def __init__(self, lat, lon, altitude=0.0, heading=0.0):
        self.lat = lat
        self.lon = lon
        self.altitude = altitude
        self.heading = heading  # degrees, 0-360
        self.speed = 0.0  # ground speed m/s
        self.vertical_speed = 0.0  # m/s, positive = ascending
        self.vx = 0.0  # velocity north m/s
        self.vy = 0.0  # velocity east m/s
        self.vz = 0.0  # velocity down m/s (NED, so negative = up)

    @property
    def ground_speed(self):
        return self.speed

    def update(self, dt, target_waypoint=None, target_altitude=None, cruise_speed=10.0):
        """
        Update position for one timestep.

        target_waypoint: (lat, lon) or None
        target_altitude: float or None
        cruise_speed: desired speed in m/s
        dt: time step in seconds

        Returns: (waypoint_reached: bool, distance_to_waypoint: float)
        """
        waypoint_reached = False
        dist_to_wp = float('inf')

        # --- Heading adjustment ---
        if target_waypoint is not None:
            target_lat, target_lon = target_waypoint
            dist_to_wp = haversine_distance(self.lat, self.lon, target_lat, target_lon)

            target_bearing = calculate_bearing(self.lat, self.lon, target_lat, target_lon)

            # Compute shortest angle difference
            diff = (target_bearing - self.heading + 540) % 360 - 180
            max_turn = TURN_RATE * dt
            if abs(diff) <= max_turn:
                self.heading = target_bearing
            elif diff > 0:
                self.heading = normalize_angle(self.heading + max_turn)
            else:
                self.heading = normalize_angle(self.heading - max_turn)

            # --- Speed control ---
            target_speed = min(cruise_speed, MAX_SPEED)

            # Decelerate within 50m of waypoint
            if dist_to_wp < 50:
                decel_speed = max(2.0, target_speed * (dist_to_wp / 50.0))
                target_speed = min(target_speed, decel_speed)

            # Apply acceleration limit
            speed_diff = target_speed - self.speed
            max_accel = ACCELERATION * dt
            if abs(speed_diff) <= max_accel:
                self.speed = target_speed
            elif speed_diff > 0:
                self.speed += max_accel
            else:
                self.speed -= max_accel

            self.speed = max(0.0, min(self.speed, MAX_SPEED))

            # Check waypoint reached (5m horizontal, 2m vertical)
            alt_diff = abs(self.altitude - (target_altitude or self.altitude))
            if dist_to_wp <= 5.0 and alt_diff <= 2.0:
                waypoint_reached = True

        else:
            # No waypoint — decelerate to stop
            if self.speed > 0:
                self.speed = max(0.0, self.speed - ACCELERATION * dt)

        # --- Position update ---
        heading_rad = math.radians(self.heading)
        vn = self.speed * math.cos(heading_rad)  # north velocity
        ve = self.speed * math.sin(heading_rad)  # east velocity

        dlat = vn * dt / METERS_PER_DEG_LAT
        meters_per_deg_lon = METERS_PER_DEG_LAT * math.cos(math.radians(self.lat))
        dlon = ve * dt / meters_per_deg_lon if meters_per_deg_lon > 0 else 0

        self.lat += dlat
        self.lon += dlon

        # --- Altitude control ---
        if target_altitude is not None:
            alt_diff = target_altitude - self.altitude
            if abs(alt_diff) < 0.1:
                self.altitude = target_altitude
                self.vertical_speed = 0.0
            elif alt_diff > 0:
                self.vertical_speed = ASCENT_RATE
                self.altitude += ASCENT_RATE * dt
                if self.altitude > target_altitude:
                    self.altitude = target_altitude
            else:
                self.vertical_speed = -DESCENT_RATE
                self.altitude -= DESCENT_RATE * dt
                if self.altitude < target_altitude:
                    self.altitude = target_altitude

        # Cap altitude
        self.altitude = max(0.0, min(self.altitude, MAX_ALTITUDE))

        # Update velocity components (NED frame)
        self.vx = vn
        self.vy = ve
        self.vz = -self.vertical_speed  # NED: positive z = down

        return waypoint_reached, dist_to_wp
