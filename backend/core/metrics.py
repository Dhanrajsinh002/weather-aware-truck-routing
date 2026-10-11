"""Segment ownership and route risk aggregation metrics.

Pure Python, no external libraries, no I/O.
"""

from __future__ import annotations

from typing import List, Sequence
from backend.core.types import Checkpoint, RiskLevel, RouteMetrics


def compute_segment_ownership(
    checkpoints: Sequence[Checkpoint],
    total_distance_miles: float,
) -> List[Checkpoint]:
    """Compute and assign owned_miles for each checkpoint.

    Rule (D9):
    A checkpoint owns the stretch from the midpoint to the previous checkpoint
    to the midpoint to the next (clamped to route ends [0, total_distance_miles]).
    """
    if not checkpoints:
        return []

    n = len(checkpoints)
    if n == 1:
        checkpoints[0].owned_miles = max(0.0, total_distance_miles)
        return list(checkpoints)

    for i in range(n):
        if i == 0:
            # Origin owns [0, (m0 + m1) / 2]
            mid_next = (checkpoints[0].mile + checkpoints[1].mile) / 2.0
            owned = mid_next - 0.0
        elif i == n - 1:
            # Destination owns [(m_{n-2} + m_{n-1}) / 2, total_distance_miles]
            mid_prev = (checkpoints[n - 2].mile + checkpoints[n - 1].mile) / 2.0
            owned = total_distance_miles - mid_prev
        else:
            # Intermediate checkpoint owns [(m_{i-1} + m_i) / 2, (m_i + m_{i+1}) / 2]
            mid_prev = (checkpoints[i - 1].mile + checkpoints[i].mile) / 2.0
            mid_next = (checkpoints[i].mile + checkpoints[i + 1].mile) / 2.0
            owned = mid_next - mid_prev

        checkpoints[i].owned_miles = max(0.0, owned)

    return list(checkpoints)


def compute_route_metrics(
    checkpoints: Sequence[Checkpoint],
    total_distance_miles: float,
) -> RouteMetrics:
    """Calculate aggregated route risk metrics.

    Rules:
    - no_travel_miles, severe_miles, high_miles: sum of owned miles at that level
    - avg_risk: distance-weighted mean of numeric levels
    - max_level: highest level observed among checkpoints
    - Miles rounded to 1 decimal, avg_risk to 2 decimals.
    """
    if not checkpoints:
        return RouteMetrics(
            no_travel_miles=0.0,
            severe_miles=0.0,
            high_miles=0.0,
            avg_risk=0.0,
            max_level=RiskLevel.LOW,
        )

    no_travel = 0.0
    severe = 0.0
    high = 0.0
    total_weighted_risk = 0.0
    total_owned = 0.0
    max_lvl = RiskLevel.LOW

    for cp in checkpoints:
        score = cp.risk.score if cp.risk else 0
        lvl = cp.risk.level if cp.risk else RiskLevel.LOW
        miles = cp.owned_miles

        if lvl > max_lvl:
            max_lvl = lvl

        if lvl == RiskLevel.NO_TRAVEL:
            no_travel += miles
        elif lvl == RiskLevel.SEVERE:
            severe += miles
        elif lvl == RiskLevel.HIGH:
            high += miles

        total_weighted_risk += miles * score
        total_owned += miles

    dist = total_distance_miles if total_distance_miles > 0 else total_owned
    avg_risk = (total_weighted_risk / dist) if dist > 0 else (checkpoints[0].risk.score if checkpoints[0].risk else 0.0)

    return RouteMetrics(
        no_travel_miles=round(no_travel, 1),
        severe_miles=round(severe, 1),
        high_miles=round(high, 1),
        avg_risk=round(avg_risk, 2),
        max_level=max_lvl,
    )
