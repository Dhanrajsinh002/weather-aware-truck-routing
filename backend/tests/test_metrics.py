import pytest
from datetime import datetime, timezone
from backend.core.types import RiskLevel, RiskResult, Checkpoint, RouteMetrics
from backend.core.metrics import (
    compute_segment_ownership,
    compute_route_metrics,
)


def test_segment_ownership_hand_computed():
    now = datetime.now(timezone.utc)
    # 5 checkpoints at miles 0, 25, 50, 75, 100
    cps = [
        Checkpoint(index=0, mile=0.0, lat=40.0, lng=-80.0, eta=now),
        Checkpoint(index=1, mile=25.0, lat=40.0, lng=-80.0, eta=now),
        Checkpoint(index=2, mile=50.0, lat=40.0, lng=-80.0, eta=now),
        Checkpoint(index=3, mile=75.0, lat=40.0, lng=-80.0, eta=now),
        Checkpoint(index=4, mile=100.0, lat=40.0, lng=-80.0, eta=now),
    ]

    compute_segment_ownership(cps, total_distance_miles=100.0)

    assert pytest.approx(cps[0].owned_miles) == 12.5
    assert pytest.approx(cps[1].owned_miles) == 25.0
    assert pytest.approx(cps[2].owned_miles) == 25.0
    assert pytest.approx(cps[3].owned_miles) == 25.0
    assert pytest.approx(cps[4].owned_miles) == 12.5
    assert pytest.approx(sum(cp.owned_miles for cp in cps)) == 100.0


def test_route_metrics_hand_computed():
    now = datetime.now(timezone.utc)
    cps = [
        Checkpoint(
            index=0,
            mile=0.0,
            lat=40.0,
            lng=-80.0,
            eta=now,
            risk=RiskResult(level=RiskLevel.LOW, score=0),
        ),
        Checkpoint(
            index=1,
            mile=25.0,
            lat=40.0,
            lng=-80.0,
            eta=now,
            risk=RiskResult(level=RiskLevel.MODERATE, score=1),
        ),
        Checkpoint(
            index=2,
            mile=50.0,
            lat=40.0,
            lng=-80.0,
            eta=now,
            risk=RiskResult(level=RiskLevel.HIGH, score=2),
        ),
        Checkpoint(
            index=3,
            mile=75.0,
            lat=40.0,
            lng=-80.0,
            eta=now,
            risk=RiskResult(level=RiskLevel.SEVERE, score=3),
        ),
        Checkpoint(
            index=4,
            mile=100.0,
            lat=40.0,
            lng=-80.0,
            eta=now,
            risk=RiskResult(level=RiskLevel.NO_TRAVEL, score=4),
        ),
    ]

    compute_segment_ownership(cps, total_distance_miles=100.0)
    metrics = compute_route_metrics(cps, total_distance_miles=100.0)

    assert metrics.no_travel_miles == 12.5
    assert metrics.severe_miles == 25.0
    assert metrics.high_miles == 25.0
    assert metrics.avg_risk == 2.00
    assert metrics.max_level == RiskLevel.NO_TRAVEL


def test_route_metrics_single_checkpoint():
    now = datetime.now(timezone.utc)
    cps = [
        Checkpoint(
            index=0,
            mile=0.0,
            lat=40.0,
            lng=-80.0,
            eta=now,
            risk=RiskResult(level=RiskLevel.LOW, score=0),
        )
    ]
    compute_segment_ownership(cps, total_distance_miles=0.0)
    metrics = compute_route_metrics(cps, total_distance_miles=0.0)
    assert metrics.no_travel_miles == 0.0
    assert metrics.severe_miles == 0.0
    assert metrics.high_miles == 0.0
    assert metrics.avg_risk == 0.0
    assert metrics.max_level == RiskLevel.LOW
