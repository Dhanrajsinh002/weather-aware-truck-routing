"""Geographic utilities and distance calculations.

Pure Python, no external geospatial libraries, no I/O.
"""

from __future__ import annotations

import math
from typing import List, Sequence, Tuple
from backend.core.types import LatLng

EARTH_RADIUS_MILES = 3958.7613


def haversine_distance_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on Earth in miles."""
    if lat1 == lat2 and lon1 == lon2:
        return 0.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    # Clamp for numerical precision issues
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return EARTH_RADIUS_MILES * c


def linestring_cumulative_distances(coordinates: Sequence[Sequence[float]]) -> List[float]:
    """Calculate cumulative distances in miles along a GeoJSON LineString coordinates list.

    coordinates: list of [lng, lat] (or [lng, lat, ...])
    Returns a list of cumulative distances starting with 0.0 at coordinates[0].
    """
    if not coordinates:
        return []

    cumulative = [0.0]
    total = 0.0
    for i in range(1, len(coordinates)):
        lon1, lat1 = coordinates[i - 1][0], coordinates[i - 1][1]
        lon2, lat2 = coordinates[i][0], coordinates[i][1]
        d = haversine_distance_miles(lat1, lon1, lat2, lon2)
        total += d
        cumulative.append(total)

    return cumulative


def total_linestring_distance(coordinates: Sequence[Sequence[float]]) -> float:
    """Compute total length in miles of a LineString."""
    cum = linestring_cumulative_distances(coordinates)
    return cum[-1] if cum else 0.0


def point_at_mile(
    coordinates: Sequence[Sequence[float]],
    target_mile: float,
    cumulative_distances: Sequence[float] | None = None,
) -> LatLng:
    """Find interpolated geographic point (LatLng) at target_mile along a LineString.

    coordinates: list of [lng, lat]
    """
    if not coordinates:
        raise ValueError("Cannot find point on empty coordinates list")

    if len(coordinates) == 1:
        return LatLng(lat=coordinates[0][1], lng=coordinates[0][0])

    if cumulative_distances is None:
        cumulative_distances = linestring_cumulative_distances(coordinates)

    total_dist = cumulative_distances[-1]
    if target_mile <= 0.0:
        return LatLng(lat=coordinates[0][1], lng=coordinates[0][0])
    if target_mile >= total_dist:
        return LatLng(lat=coordinates[-1][1], lng=coordinates[-1][0])

    # Find the segment containing target_mile
    for i in range(1, len(cumulative_distances)):
        d_end = cumulative_distances[i]
        d_start = cumulative_distances[i - 1]
        if d_start <= target_mile <= d_end:
            segment_len = d_end - d_start
            if segment_len <= 1e-9:
                return LatLng(lat=coordinates[i][1], lng=coordinates[i][0])
            fraction = (target_mile - d_start) / segment_len

            lon1, lat1 = coordinates[i - 1][0], coordinates[i - 1][1]
            lon2, lat2 = coordinates[i][0], coordinates[i][1]

            interp_lat = lat1 + fraction * (lat2 - lat1)
            interp_lon = lon1 + fraction * (lon2 - lon1)
            return LatLng(lat=interp_lat, lng=interp_lon)

    return LatLng(lat=coordinates[-1][1], lng=coordinates[-1][0])
