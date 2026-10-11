"""ETA calculation along routes.

Pure Python, no external libraries, no I/O.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Sequence, Tuple
from backend.core.types import Checkpoint


def eta_at_mile(
    mile: float,
    total_distance_miles: float,
    total_duration_seconds: float,
    departure: datetime,
    time_profile: Sequence[Tuple[float, float]] | None = None,
) -> datetime:
    """Calculate the estimated time of arrival (ETA) at a specific mileage along a route.

    If time_profile is given as a list of (cumulative_mile, cumulative_seconds),
    linear interpolation between profile points is used.
    Otherwise, proportional interpolation by distance is used as a fallback.

    Always guarantees:
    - Exactly departure at mile 0.0
    - Exactly departure + total_duration_seconds at total_distance_miles
    - Monotonic non-decreasing in mile
    """
    if total_distance_miles <= 0.0 or total_duration_seconds <= 0.0:
        return departure

    if mile <= 0.0:
        return departure

    if mile >= total_distance_miles:
        return departure + timedelta(seconds=float(total_duration_seconds))

    elapsed_seconds: float

    if time_profile and len(time_profile) >= 2:
        # Interpolate using distance-time profile
        # Find bracketing segment
        for i in range(1, len(time_profile)):
            m_start, s_start = time_profile[i - 1]
            m_end, s_end = time_profile[i]
            if m_start <= mile <= m_end:
                span_mile = m_end - m_start
                if span_mile <= 1e-9:
                    elapsed_seconds = s_start
                else:
                    fraction = (mile - m_start) / span_mile
                    elapsed_seconds = s_start + fraction * (s_end - s_start)
                break
        else:
            # Beyond profile end
            elapsed_seconds = time_profile[-1][1]
    else:
        # Fallback: proportional by distance
        fraction = mile / total_distance_miles
        elapsed_seconds = fraction * total_duration_seconds

    # Clamp between 0 and total duration
    elapsed_seconds = max(0.0, min(float(total_duration_seconds), elapsed_seconds))
    return departure + timedelta(seconds=elapsed_seconds)


def compute_checkpoints_eta(
    checkpoints: Sequence[Checkpoint],
    total_distance_miles: float,
    total_duration_seconds: float,
    departure: datetime,
    time_profile: Sequence[Tuple[float, float]] | None = None,
) -> List[Checkpoint]:
    """Assign monotonic ETAs to all checkpoints along a route."""
    result: List[Checkpoint] = []
    for cp in checkpoints:
        eta = eta_at_mile(
            cp.mile,
            total_distance_miles,
            total_duration_seconds,
            departure,
            time_profile=time_profile,
        )
        cp.eta = eta
        result.append(cp)
    return result
