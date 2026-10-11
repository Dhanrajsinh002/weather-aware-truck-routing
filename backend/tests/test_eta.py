import pytest
from datetime import datetime, timezone, timedelta
from backend.core.eta import eta_at_mile, compute_checkpoints_eta
from backend.core.types import Checkpoint


def test_eta_endpoints_exact_proportional():
    dep = datetime(2026, 10, 12, 14, 0, 0, tzinfo=timezone.utc)
    total_dist = 1000.0
    total_duration = 54000.0  # 15 hours

    eta_start = eta_at_mile(0.0, total_dist, total_duration, dep)
    assert eta_start == dep

    eta_end = eta_at_mile(total_dist, total_dist, total_duration, dep)
    assert eta_end == dep + timedelta(seconds=total_duration)

    eta_mid = eta_at_mile(500.0, total_dist, total_duration, dep)
    assert eta_mid == dep + timedelta(seconds=27000.0)


def test_eta_with_profile():
    dep = datetime(2026, 10, 12, 14, 0, 0, tzinfo=timezone.utc)
    # Profile: fast highway first 100 miles (1 hour), slow mountain next 100 miles (2 hours)
    profile = [
        (0.0, 0.0),
        (100.0, 3600.0),
        (200.0, 10800.0),
    ]
    # At 50 miles -> 1800 s (0.5 hr)
    eta_50 = eta_at_mile(50.0, 200.0, 10800.0, dep, time_profile=profile)
    assert eta_50 == dep + timedelta(seconds=1800.0)

    # At 150 miles -> 3600 + 3600 = 7200 s (2 hr)
    eta_150 = eta_at_mile(150.0, 200.0, 10800.0, dep, time_profile=profile)
    assert eta_150 == dep + timedelta(seconds=7200.0)


def test_eta_monotonicity():
    dep = datetime(2026, 10, 12, 14, 0, 0, tzinfo=timezone.utc)
    total_dist = 500.0
    total_duration = 30000.0

    profile = [
        (0.0, 0.0),
        (100.0, 5000.0),
        (300.0, 18000.0),
        (500.0, 30000.0),
    ]

    miles = [0.0, 25.0, 50.0, 100.0, 150.0, 250.0, 300.0, 400.0, 500.0]
    etas = [eta_at_mile(m, total_dist, total_duration, dep, time_profile=profile) for m in miles]

    for i in range(1, len(etas)):
        assert etas[i] >= etas[i - 1]


def test_eta_zero_distance():
    dep = datetime(2026, 10, 12, 14, 0, 0, tzinfo=timezone.utc)
    assert eta_at_mile(0.0, 0.0, 0.0, dep) == dep


def test_compute_checkpoints_eta():
    dep = datetime(2026, 10, 12, 14, 0, 0, tzinfo=timezone.utc)
    cps = [
        Checkpoint(index=0, mile=0.0, lat=40.0, lng=-80.0, eta=dep),
        Checkpoint(index=1, mile=50.0, lat=40.5, lng=-80.0, eta=dep),
        Checkpoint(index=2, mile=100.0, lat=41.0, lng=-80.0, eta=dep),
    ]
    updated = compute_checkpoints_eta(cps, total_distance_miles=100.0, total_duration_seconds=7200.0, departure=dep)
    assert updated[0].eta == dep
    assert updated[1].eta == dep + timedelta(seconds=3600.0)
    assert updated[2].eta == dep + timedelta(seconds=7200.0)
