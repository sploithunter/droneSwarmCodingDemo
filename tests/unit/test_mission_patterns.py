"""Unit tests for mission pattern generators."""
import pytest
from mission.mission_patterns import (
    CENTER_LAT, CENTER_LON,
    perimeter_patrol, grid_north, grid_south,
    radial_survey, diagonal_cross, circle_patrol, point_inspection
)

ALL_PATTERNS = [
    perimeter_patrol, grid_north, grid_south,
    radial_survey, diagonal_cross, circle_patrol, point_inspection
]


def test_perimeter_has_8_waypoints():
    assert len(perimeter_patrol()) == 8


def test_grid_north_has_12_waypoints():
    assert len(grid_north()) == 12


def test_grid_south_has_12_waypoints():
    assert len(grid_south()) == 12


def test_radial_has_8_waypoints():
    assert len(radial_survey()) == 8


def test_diagonal_has_6_waypoints():
    assert len(diagonal_cross()) == 6


def test_circle_has_16_waypoints():
    assert len(circle_patrol()) == 16


def test_point_inspection_has_4_waypoints():
    assert len(point_inspection()) == 4


def test_all_patterns_within_bounds():
    """All waypoints must be within ±0.01 deg lat and ±0.013 deg lon of center."""
    for pattern_fn in ALL_PATTERNS:
        waypoints = pattern_fn()
        for wp in waypoints:
            assert abs(wp["latitude"] - CENTER_LAT) <= 0.01, (
                f"{pattern_fn.__name__}: lat {wp['latitude']} out of bounds"
            )
            assert abs(wp["longitude"] - CENTER_LON) <= 0.013, (
                f"{pattern_fn.__name__}: lon {wp['longitude']} out of bounds"
            )


def test_waypoints_have_altitude():
    """All waypoints must have altitude_m > 0."""
    for pattern_fn in ALL_PATTERNS:
        waypoints = pattern_fn()
        for wp in waypoints:
            assert wp["altitude_m"] > 0, (
                f"{pattern_fn.__name__}: altitude_m must be > 0"
            )
