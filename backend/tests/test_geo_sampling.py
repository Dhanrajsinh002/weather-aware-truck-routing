import pytest
import math
from backend.core.types import LatLng
from backend.core.geo import (
    haversine_distance_miles,
    linestring_cumulative_distances,
    total_linestring_distance,
    point_at_mile,
    EARTH_RADIUS_MILES,
)
from backend.core.sampling import (
    auto_interval,
    sample_checkpoint_miles,
    sample_checkpoints,
)


def test_haversine_known_distance():
    # Chicago (41.8781, -87.6298) to Denver (39.7392, -104.9903) ~ 918-920 miles great circle
    chicago = (41.8781, -87.6298)
    denver = (39.7392, -104.9903)
    d = haversine_distance_miles(chicago[0], chicago[1], denver[0], denver[1])
    assert 915 < d < 925


def test_haversine_zero():
    assert haversine_distance_miles(40.0, -80.0, 40.0, -80.0) == 0.0


def test_auto_interval():
    assert auto_interval(100.0) == 10
    assert auto_interval(249.9) == 10
    assert auto_interval(250.0) == 25
    assert auto_interval(799.9) == 25
    assert auto_interval(800.0) == 50
    assert auto_interval(1200.0) == 50


def test_synthetic_linestring_point_at_mile():
    # Straight line east along equator: (lat=0, lng=0) to (lat=0, lng=10)
    coords = [[0.0, 0.0], [5.0, 0.0], [10.0, 0.0]]  # [lng, lat]
    cum_dist = linestring_cumulative_distances(coords)
    total_dist = cum_dist[-1]
    assert total_dist > 600

    # Start point
    pt_start = point_at_mile(coords, 0.0, cum_dist)
    assert pytest.approx(pt_start.lat, abs=1e-5) == 0.0
    assert pytest.approx(pt_start.lng, abs=1e-5) == 0.0

    # Mid point
    half_dist = total_dist / 2.0
    pt_mid = point_at_mile(coords, half_dist, cum_dist)
    assert pytest.approx(pt_mid.lat, abs=1e-5) == 0.0
    assert pytest.approx(pt_mid.lng, abs=1e-4) == 5.0

    # End point
    pt_end = point_at_mile(coords, total_dist, cum_dist)
    assert pytest.approx(pt_end.lat, abs=1e-5) == 0.0
    assert pytest.approx(pt_end.lng, abs=1e-5) == 10.0


def test_sample_checkpoint_miles():
    # 100 miles with interval 25
    miles = sample_checkpoint_miles(100.0, interval_miles=25)
    assert miles == [0.0, 25.0, 50.0, 75.0, 100.0]

    # 105 miles with interval 25 -> includes 100 and final 105
    miles_uneven = sample_checkpoint_miles(105.0, interval_miles=25)
    assert miles_uneven == [0.0, 25.0, 50.0, 75.0, 100.0, 105.0]

    # Very short trip: 12 miles with interval 25 -> 0.0 and 12.0
    miles_short = sample_checkpoint_miles(12.0, interval_miles=25)
    assert miles_short == [0.0, 12.0]

    # Zero distance
    assert sample_checkpoint_miles(0.0, interval_miles=25) == [0.0]


def test_sample_checkpoints_spacing_and_endpoints():
    # Construct a synthetic line of exact length 100.0 miles
    lat_start = 40.0
    lng = -80.0
    delta_deg = math.degrees(100.0 / EARTH_RADIUS_MILES)
    lat_end = lat_start + delta_deg
    coords = [[lng, lat_start], [lng, (lat_start + lat_end) / 2.0], [lng, lat_end]]

    samples = sample_checkpoints(coords, interval_miles=25)
    assert len(samples) == 5
    assert samples[0].index == 0
    assert samples[0].mile == 0.0
    assert pytest.approx(samples[0].lat, abs=1e-4) == lat_start
    assert pytest.approx(samples[0].lng, abs=1e-4) == lng

    assert samples[-1].index == 4
    assert pytest.approx(samples[-1].mile, abs=0.01) == 100.0
    assert pytest.approx(samples[-1].lat, abs=1e-4) == lat_end

    # Check intermediate spacing within 0.5%
    for i in range(1, len(samples)):
        step = samples[i].mile - samples[i - 1].mile
        assert abs(step - 25.0) / 25.0 < 0.005
