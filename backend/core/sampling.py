"""Checkpoint sampling along routes.

Pure Python, no external libraries, no I/O.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Sequence
from backend.core.geo import (
    linestring_cumulative_distances,
    point_at_mile,
)
from backend.core.types import Checkpoint


def auto_interval(total_miles: float) -> int:
    """Determine automatic checkpoint interval based on total route distance.

    Rules:
    - total_miles < 250 -> 10 mi
    - total_miles < 800 -> 25 mi
    - otherwise -> 50 mi
    """
    if total_miles < 250.0:
        return 10
    if total_miles < 800.0:
        return 25
    return 50


def sample_checkpoint_miles(total_miles: float, interval_miles: float) -> List[float]:
    """Generate target mileage values for checkpoints along a route.

    Always includes 0.0 (start) and total_miles (end).
    If the final step to total_miles is negligible (< 0.25 miles), snap to total_miles.
    """
    if total_miles <= 0.0:
        return [0.0]

    miles = [0.0]
    current = float(interval_miles)
    snap_threshold = min(0.5, float(interval_miles) * 0.05)

    while current < (total_miles - snap_threshold):
        miles.append(round(current, 2))
        current += float(interval_miles)

    # Always include destination point if not already added
    if abs(miles[-1] - total_miles) > 1e-4:
        miles.append(round(total_miles, 2))

    return miles


def sample_checkpoints(
    coordinates: Sequence[Sequence[float]],
    interval_miles: float,
    default_eta: datetime | None = None,
) -> List[Checkpoint]:
    """Sample checkpoints along a route geometry given an interval.

    coordinates: GeoJSON coordinates [[lng, lat], ...]
    Always includes origin (mile 0.0) and destination (total_miles).
    """
    if not coordinates:
        return []

    cum_dist = linestring_cumulative_distances(coordinates)
    total_dist = cum_dist[-1]
    target_miles = sample_checkpoint_miles(total_dist, interval_miles)

    if default_eta is None:
        default_eta = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    checkpoints: List[Checkpoint] = []
    for idx, mile in enumerate(target_miles):
        pt = point_at_mile(coordinates, mile, cum_dist)
        checkpoints.append(
            Checkpoint(
                index=idx,
                mile=round(mile, 2),
                lat=round(pt.lat, 5),
                lng=round(pt.lng, 5),
                eta=default_eta,
            )
        )

    return checkpoints
