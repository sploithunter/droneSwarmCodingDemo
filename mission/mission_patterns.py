"""Mission pattern generators for drone swarm."""
import math

CENTER_LAT = 37.3861
CENTER_LON = -122.0839
AREA_SIZE_M = 2000  # 2km x 2km

# Conversion factors at this latitude
METERS_PER_DEG_LAT = 111320.0
METERS_PER_DEG_LON = 111320.0 * math.cos(math.radians(CENTER_LAT))

# Half-size in degrees
HALF_LAT = (AREA_SIZE_M / 2) / METERS_PER_DEG_LAT
HALF_LON = (AREA_SIZE_M / 2) / METERS_PER_DEG_LON


def _geo(lat, lon, alt=50.0):
    """Create a waypoint dict."""
    return {"latitude": lat, "longitude": lon, "altitude_m": alt}


def perimeter_patrol(altitude=50.0):
    """8 waypoints forming a rectangle around the boundary."""
    n = CENTER_LAT + HALF_LAT * 0.9
    s = CENTER_LAT - HALF_LAT * 0.9
    e = CENTER_LON + HALF_LON * 0.9
    w = CENTER_LON - HALF_LON * 0.9
    return [
        _geo(n, w, altitude), _geo(n, CENTER_LON, altitude),
        _geo(n, e, altitude), _geo(CENTER_LAT, e, altitude),
        _geo(s, e, altitude), _geo(s, CENTER_LON, altitude),
        _geo(s, w, altitude), _geo(CENTER_LAT, w, altitude),
    ]


def grid_north(altitude=50.0):
    """12 waypoints: lawn-mower pattern over north half."""
    n = CENTER_LAT + HALF_LAT * 0.9
    mid = CENTER_LAT
    e = CENTER_LON + HALF_LON * 0.8
    w = CENTER_LON - HALF_LON * 0.8
    rows = 6
    waypoints = []
    for i in range(rows):
        lat = mid + (n - mid) * (i / (rows - 1))
        if i % 2 == 0:
            waypoints.append(_geo(lat, w, altitude))
            waypoints.append(_geo(lat, e, altitude))
        else:
            waypoints.append(_geo(lat, e, altitude))
            waypoints.append(_geo(lat, w, altitude))
    return waypoints


def grid_south(altitude=50.0):
    """12 waypoints: lawn-mower pattern over south half."""
    s = CENTER_LAT - HALF_LAT * 0.9
    mid = CENTER_LAT
    e = CENTER_LON + HALF_LON * 0.8
    w = CENTER_LON - HALF_LON * 0.8
    rows = 6
    waypoints = []
    for i in range(rows):
        lat = mid - (mid - s) * (i / (rows - 1))
        if i % 2 == 0:
            waypoints.append(_geo(lat, w, altitude))
            waypoints.append(_geo(lat, e, altitude))
        else:
            waypoints.append(_geo(lat, e, altitude))
            waypoints.append(_geo(lat, w, altitude))
    return waypoints


def radial_survey(altitude=60.0):
    """8 waypoints: star pattern from center outward."""
    waypoints = []
    for i in range(8):
        angle = i * 45
        r = HALF_LAT * 0.8
        lat = CENTER_LAT + r * math.cos(math.radians(angle))
        lon_r = HALF_LON * 0.8
        lon = CENTER_LON + lon_r * math.sin(math.radians(angle))
        waypoints.append(_geo(lat, lon, altitude))
    return waypoints


def diagonal_cross(altitude=55.0):
    """6 waypoints: X pattern across the area."""
    d_lat = HALF_LAT * 0.85
    d_lon = HALF_LON * 0.85
    return [
        _geo(CENTER_LAT + d_lat, CENTER_LON - d_lon, altitude),
        _geo(CENTER_LAT - d_lat, CENTER_LON + d_lon, altitude),
        _geo(CENTER_LAT, CENTER_LON, altitude),
        _geo(CENTER_LAT + d_lat, CENTER_LON + d_lon, altitude),
        _geo(CENTER_LAT - d_lat, CENTER_LON - d_lon, altitude),
        _geo(CENTER_LAT, CENTER_LON, altitude),
    ]


def circle_patrol(altitude=45.0):
    """16 waypoints: large circle around the area."""
    waypoints = []
    radius_lat = HALF_LAT * 0.85
    radius_lon = HALF_LON * 0.85
    for i in range(16):
        angle = i * (360 / 16)
        lat = CENTER_LAT + radius_lat * math.cos(math.radians(angle))
        lon = CENTER_LON + radius_lon * math.sin(math.radians(angle))
        waypoints.append(_geo(lat, lon, altitude))
    return waypoints


def point_inspection(altitude=70.0):
    """4 waypoints: direct flights between 4 distant points."""
    d_lat = HALF_LAT * 0.7
    d_lon = HALF_LON * 0.7
    return [
        _geo(CENTER_LAT + d_lat, CENTER_LON + d_lon, altitude),
        _geo(CENTER_LAT - d_lat, CENTER_LON - d_lon, altitude),
        _geo(CENTER_LAT + d_lat, CENTER_LON - d_lon, altitude),
        _geo(CENTER_LAT - d_lat, CENTER_LON + d_lon, altitude),
    ]
