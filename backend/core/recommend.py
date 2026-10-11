"""Route ranking and recommendation rationale generation.

Pure Python, no external libraries, no I/O.
"""

from __future__ import annotations

from typing import List, Tuple
from backend.core.types import Recommendation, Route


def rank_key(route: Route) -> Tuple[float, float, float, float, float]:
    """Lexicographic comparison key for route preference order.

    1. fewest No Travel miles (rounded 1 dec)
    2. fewest Severe miles (rounded 1 dec)
    3. fewest High miles (rounded 1 dec)
    4. lowest average risk (rounded 2 dec)
    5. shortest travel time (duration in seconds)
    """
    m = route.metrics
    if m is None:
        return (0.0, 0.0, 0.0, 0.0, route.duration_seconds)
    return (
        round(m.no_travel_miles, 1),
        round(m.severe_miles, 1),
        round(m.high_miles, 1),
        round(m.avg_risk, 2),
        route.duration_seconds,
    )


def generate_recommendation_reasons(winner: Route, others: List[Route]) -> List[str]:
    """Generate comparative reasons explaining why the winner was chosen over alternatives."""
    if not others:
        return ["Only route option evaluated."]

    reasons: List[str] = []
    wm = winner.metrics

    if wm is None:
        return ["Best overall balance of weather safety and travel time."]

    other_metrics = [r.metrics for r in others if r.metrics is not None]
    if not other_metrics:
        return ["Safest route available based on weather forecast."]

    # 1. Compare No Travel miles
    other_nt = [round(m.no_travel_miles, 1) for m in other_metrics]
    if round(wm.no_travel_miles, 1) < min(other_nt):
        if round(wm.no_travel_miles, 1) == 0.0:
            nt_str = ", ".join(f"{x:.1f}" for x in other_nt)
            reasons.append(f"Avoids No Travel conditions present on alternatives ({nt_str} mi)")
        else:
            nt_str = ", ".join(f"{x:.1f}" for x in other_nt)
            reasons.append(f"Fewest No Travel miles ({wm.no_travel_miles:.1f} vs {nt_str})")

    # 2. Compare Severe miles
    other_sev = [round(m.severe_miles, 1) for m in other_metrics]
    if round(wm.severe_miles, 1) < min(other_sev):
        sev_str = ", ".join(f"{x:.1f}" for x in other_sev)
        reasons.append(f"Fewest Severe miles ({wm.severe_miles:.1f} vs {sev_str})")

    # 3. Compare High risk miles
    other_high = [round(m.high_miles, 1) for m in other_metrics]
    if round(wm.high_miles, 1) < min(other_high) and round(wm.severe_miles, 1) <= min(other_sev):
        high_str = ", ".join(f"{x:.1f}" for x in other_high)
        reasons.append(f"Fewest High risk miles ({wm.high_miles:.1f} vs {high_str})")

    # 4. Compare average risk
    other_avg = [round(m.avg_risk, 2) for m in other_metrics]
    if round(wm.avg_risk, 2) < min(other_avg):
        avg_str = ", ".join(f"{x:.2f}" for x in other_avg)
        reasons.append(f"Lowest average weather risk ({wm.avg_risk:.2f} vs {avg_str})")

    # 5. Compare duration
    other_dur = [r.duration_seconds for r in others]
    if winner.duration_seconds < min(other_dur):
        win_hrs = winner.duration_seconds / 3600.0
        dur_str = ", ".join(f"{d / 3600.0:.1f}" for d in other_dur)
        reasons.append(f"Fastest travel time ({win_hrs:.1f} h vs {dur_str} h)")

    # Fallback if identical on all comparative factors
    if not reasons:
        reasons.append("Optimal route choice balancing weather risk and transit duration.")

    return reasons


def rank_and_recommend_routes(routes: List[Route]) -> Tuple[List[Route], Recommendation]:
    """Rank routes lexicographically and generate recommendation."""
    if not routes:
        return [], Recommendation(route_id="", reasons=[], warnings=["No routes available."])

    # Sort routes according to lexicographic preference order
    sorted_routes = sorted(routes, key=rank_key)

    # Assign ranks and recommended flag
    for idx, route in enumerate(sorted_routes):
        route.rank = idx + 1
        route.recommended = idx == 0

    winner = sorted_routes[0]
    others = sorted_routes[1:]

    reasons = generate_recommendation_reasons(winner, others)
    warnings: List[str] = []

    # Check if all routes contain No Travel
    all_no_travel = all(
        r.metrics is not None and round(r.metrics.no_travel_miles, 1) > 0.0 for r in sorted_routes
    )
    if all_no_travel:
        warnings.append(
            "All available routes encounter No Travel weather conditions. "
            "Delaying departure is strongly recommended."
        )

    if len(sorted_routes) < 3:
        warnings.append(f"Only {len(sorted_routes)} route option(s) could be identified.")

    rec = Recommendation(
        route_id=winner.id,
        reasons=reasons,
        warnings=warnings,
    )

    return sorted_routes, rec
