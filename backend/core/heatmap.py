"""Corridor sampling and hourly risk levels for heatmap.

Pure Python, no external libraries, no I/O.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Sequence, Set, Tuple
from backend.core.geo import linestring_cumulative_distances, point_at_mile
from backend.core.risk import classify_checkpoint
from backend.core.sampling import sample_checkpoint_miles
from backend.core.types import HeatmapPoint, LatLng
from backend.core.weather_interp import HourlySeries, interpolate_weather_at_time


def round_to_grid(val: float, resolution: float = 0.1) -> float:
    """Round a coordinate to the nearest grid resolution."""
    return round(round(val / resolution) * resolution, 1)


def sample_corridor_points(
    route_geometries: Sequence[Sequence[Sequence[float]]],
    spacing_miles: float = 10.0,
    grid_resolution: float = 0.1,
) -> List[LatLng]:
    """Sample points along all routes every spacing_miles, de-duplicated on grid_resolution.

    route_geometries: list of GeoJSON LineString coordinates [[lng, lat], ...]
    """
    seen_cells: Set[Tuple[float, float]] = set()
    unique_points: List[LatLng] = []

    for coords in route_geometries:
        if not coords:
            continue

        cum_dist = linestring_cumulative_distances(coords)
        total_dist = cum_dist[-1]
        target_miles = sample_checkpoint_miles(total_dist, spacing_miles)

        for mile in target_miles:
            pt = point_at_mile(coords, mile, cum_dist)
            grid_lat = round_to_grid(pt.lat, grid_resolution)
            grid_lng = round_to_grid(pt.lng, grid_resolution)

            cell = (grid_lat, grid_lng)
            if cell not in seen_cells:
                seen_cells.add(cell)
                unique_points.append(LatLng(lat=grid_lat, lng=grid_lng))

    return unique_points


def compute_heatmap_point_levels(
    series: HourlySeries,
    departure_time: datetime,
    load_lb: float,
    hours: int = 49,
) -> List[int]:
    """Compute risk levels (0-4) for 0..(hours-1) hours after departure_time."""
    levels: List[int] = []

    for h in range(hours):
        instant = departure_time + timedelta(hours=h)
        weather, _ = interpolate_weather_at_time(series, instant)
        risk = classify_checkpoint(weather, load_lb)
        levels.append(int(risk.level))

    return levels


def build_corridor_heatmap(
    route_geometries: Sequence[Sequence[Sequence[float]]],
    weather_lookup: Dict[Tuple[float, float], HourlySeries],
    departure_time: datetime,
    load_lb: float,
    spacing_miles: float = 10.0,
    hours: int = 49,
) -> List[HeatmapPoint]:
    """Construct heatmap payload with 49 hourly risk levels per corridor point."""
    points = sample_corridor_points(route_geometries, spacing_miles=spacing_miles)
    heatmap_points: List[HeatmapPoint] = []

    fallback_series = HourlySeries()

    for pt in points:
        key = (pt.lat, pt.lng)
        series = weather_lookup.get(key, fallback_series)
        levels = compute_heatmap_point_levels(
            series=series,
            departure_time=departure_time,
            load_lb=load_lb,
            hours=hours,
        )
        heatmap_points.append(
            HeatmapPoint(
                lat=pt.lat,
                lng=pt.lng,
                levels=levels,
            )
        )

    return heatmap_points
