import pytest
from datetime import datetime, timezone, timedelta
from backend.core.weather_interp import HourlySeries
from backend.core.heatmap import (
    sample_corridor_points,
    compute_heatmap_point_levels,
    build_corridor_heatmap,
)
from backend.core.types import RiskLevel


def test_sample_corridor_points_deduplication():
    # Two identical routes sampled every 10 miles
    coords1 = [[-87.6298, 41.8781], [-87.6298, 42.5]]
    coords2 = [[-87.6298, 41.8781], [-87.6298, 42.5]]

    points = sample_corridor_points([coords1, coords2], spacing_miles=10.0, grid_resolution=0.1)
    # De-duplicated on 0.1 deg grid
    assert len(points) > 0
    # Make sure all points are unique on 0.1 deg grid
    grid_set = {(p.lat, p.lng) for p in points}
    assert len(grid_set) == len(points)


def test_compute_heatmap_point_levels_49_hours():
    dep = datetime(2026, 10, 12, 14, 0, 0, tzinfo=timezone.utc)
    times = [dep + timedelta(hours=i) for i in range(55)]
    # First 10 hours calm, hours 10-20 moderate, hours 20-30 high, hours 30-40 severe, hours 40+ severe+heavy load -> no travel
    winds = []
    for i in range(55):
        if i < 10:
            winds.append(10.0)
        elif i < 20:
            winds.append(28.0)
        elif i < 30:
            winds.append(38.0)
        elif i < 40:
            winds.append(48.0)
        else:
            winds.append(48.0)

    series = HourlySeries(
        times=times,
        wind_mph=winds,
        gust_mph=[w * 1.2 for w in winds],
        rain_in_hr=[0.0] * 55,
        snow_in_hr=[0.0] * 55,
    )

    # Load 35,000 lb: wind 48 mph escalates to NO_TRAVEL (4)
    levels = compute_heatmap_point_levels(series, departure_time=dep, load_lb=35000, hours=49)
    assert len(levels) == 49
    assert all(0 <= lvl <= 4 for lvl in levels)

    # Hours 0-9: Low (0)
    assert levels[0] == RiskLevel.LOW
    assert levels[9] == RiskLevel.LOW
    # Hours 10-19: Moderate (1)
    assert levels[15] == RiskLevel.MODERATE
    # Hours 20-29: High (2) (wind 38 + 35k lb does not escalate to severe since 35k < 40k)
    assert levels[25] == RiskLevel.HIGH
    # Hours 30-48: wind 48 + 35,000 lb -> NO_TRAVEL (4)
    assert levels[35] == RiskLevel.NO_TRAVEL
    assert levels[48] == RiskLevel.NO_TRAVEL


def test_build_corridor_heatmap():
    dep = datetime(2026, 10, 12, 14, 0, 0, tzinfo=timezone.utc)
    times = [dep + timedelta(hours=i) for i in range(50)]
    series = HourlySeries(
        times=times,
        wind_mph=[15.0] * 50,
        gust_mph=[20.0] * 50,
        rain_in_hr=[0.0] * 50,
        snow_in_hr=[0.0] * 50,
    )

    coords = [[-87.6, 41.8], [-87.6, 42.2]]
    heatmap_points = build_corridor_heatmap(
        route_geometries=[coords],
        weather_lookup={(41.8, -87.6): series, (41.9, -87.6): series, (42.0, -87.6): series, (42.1, -87.6): series, (42.2, -87.6): series},
        departure_time=dep,
        load_lb=40000,
        spacing_miles=10.0,
        hours=49,
    )

    assert len(heatmap_points) > 0
    for hp in heatmap_points:
        assert len(hp.levels) == 49
        assert all(lvl == RiskLevel.LOW for lvl in hp.levels)
