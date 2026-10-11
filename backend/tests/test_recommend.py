import pytest
from backend.core.types import Route, RouteMetrics, RiskLevel
from backend.core.recommend import rank_and_recommend_routes


def make_route(
    route_id: str,
    label: str,
    no_travel: float = 0.0,
    severe: float = 0.0,
    high: float = 0.0,
    avg_risk: float = 0.0,
    duration: float = 3600.0,
    distance: float = 100.0,
) -> Route:
    r = Route(
        id=route_id,
        label=label,
        distance_miles=distance,
        duration_seconds=duration,
        metrics=RouteMetrics(
            no_travel_miles=no_travel,
            severe_miles=severe,
            high_miles=high,
            avg_risk=avg_risk,
            max_level=RiskLevel.LOW,
        ),
    )
    return r


def test_rule_1_prefers_fewer_no_travel_miles():
    r1 = make_route("r1", "Fast", no_travel=10.0, severe=0.0, duration=1000)
    r2 = make_route("r2", "Safe", no_travel=0.0, severe=50.0, duration=2000)

    routes, rec = rank_and_recommend_routes([r1, r2])
    assert rec.route_id == "r2"
    assert routes[0].id == "r2"
    assert routes[0].rank == 1
    assert routes[0].recommended is True
    assert routes[1].id == "r1"
    assert routes[1].rank == 2
    assert routes[1].recommended is False


def test_rule_2_prefers_fewer_severe_miles():
    r1 = make_route("r1", "More Severe", severe=30.0, high=0.0, duration=1000)
    r2 = make_route("r2", "Less Severe", severe=10.0, high=50.0, duration=2000)

    routes, rec = rank_and_recommend_routes([r1, r2])
    assert rec.route_id == "r2"
    assert any("Fewest Severe miles" in r for r in rec.reasons)


def test_rule_3_prefers_fewer_high_miles():
    r1 = make_route("r1", "More High", severe=10.0, high=40.0, duration=1000)
    r2 = make_route("r2", "Less High", severe=10.0, high=20.0, duration=2000)

    routes, rec = rank_and_recommend_routes([r1, r2])
    assert rec.route_id == "r2"
    assert any("Fewest High risk miles" in r for r in rec.reasons)


def test_rule_4_prefers_lower_avg_risk():
    r1 = make_route("r1", "Higher Avg", severe=10.0, high=20.0, avg_risk=1.50, duration=1000)
    r2 = make_route("r2", "Lower Avg", severe=10.0, high=20.0, avg_risk=1.10, duration=2000)

    routes, rec = rank_and_recommend_routes([r1, r2])
    assert rec.route_id == "r2"
    assert any("Lowest average weather risk" in r for r in rec.reasons)


def test_rule_5_prefers_shorter_duration():
    r1 = make_route("r1", "Slower", severe=10.0, high=20.0, avg_risk=1.20, duration=7200)
    r2 = make_route("r2", "Faster", severe=10.0, high=20.0, avg_risk=1.20, duration=3600)

    routes, rec = rank_and_recommend_routes([r1, r2])
    assert rec.route_id == "r2"
    assert any("Fastest travel time" in r for r in rec.reasons)


def test_all_routes_contain_no_travel_triggers_warning():
    r1 = make_route("r1", "Route 1", no_travel=25.0)
    r2 = make_route("r2", "Route 2", no_travel=40.0)

    routes, rec = rank_and_recommend_routes([r1, r2])
    assert rec.route_id == "r1"
    assert len(rec.warnings) > 0
    assert any("No Travel" in w for w in rec.warnings)


def test_winner_reasons_formatting():
    # 3 routes as in PLAN.md example
    r1 = make_route("r1", "Route 1", no_travel=0.0, severe=12.5, high=40.0, avg_risk=0.84, duration=54000)
    r2 = make_route("r2", "Route 2", no_travel=0.0, severe=31.0, high=20.0, avg_risk=1.15, duration=50000)
    r3 = make_route("r3", "Route 3", no_travel=0.0, severe=44.2, high=10.0, avg_risk=1.40, duration=52000)

    routes, rec = rank_and_recommend_routes([r1, r2, r3])
    assert rec.route_id == "r1"
    assert any("Fewest Severe miles (12.5 vs 31.0, 44.2)" in reason for reason in rec.reasons)
