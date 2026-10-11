import json
from pathlib import Path
import pytest
import httpx
from backend.core.types import LatLng
from backend.providers.base import NoRouteFoundError, RoutingError
from backend.providers.valhalla import ValhallaProvider, LB_TO_METRIC_TONS


def test_weight_conversion():
    lb = 42000.0
    tons = lb * LB_TO_METRIC_TONS
    assert pytest.approx(tons, abs=0.01) == 19.05


def test_valhalla_request_payload():
    provider = ValhallaProvider()
    origin = LatLng(lat=41.8781, lng=-87.6298)
    dest = LatLng(lat=39.7392, lng=-104.9903)
    payload = provider._build_payload(origin, dest, weight_lb=44092.4)

    assert payload["costing"] == "truck"
    assert payload["alternates"] == 2
    assert payload["units"] == "miles"
    assert pytest.approx(payload["costing_options"]["truck"]["weight"], abs=0.1) == 20.0
    assert payload["locations"][0] == {"lat": 41.8781, "lon": -87.6298}
    assert payload["locations"][1] == {"lat": 39.7392, "lon": -104.9903}


def test_parse_valhalla_fixture():
    fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "valhalla_chicago_denver.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        fixture_data = json.load(f)

    provider = ValhallaProvider()
    routes = provider._parse_response(fixture_data)

    assert len(routes) == 3
    # Main route
    r1 = routes[0]
    assert r1.id == "r1"
    assert r1.label == "Fastest"
    assert r1.distance_miles == 1003.2
    assert r1.duration_seconds == 54000.0
    assert len(r1.geometry) > 1
    # Check [lng, lat] GeoJSON ordering
    first_pt = r1.geometry[0]
    assert pytest.approx(first_pt[1], abs=0.1) == 41.8781
    assert pytest.approx(first_pt[0], abs=0.1) == -87.6298

    # Alternate 1
    r2 = routes[1]
    assert r2.id == "r2"
    assert r2.label == "Alternative 1"
    assert r2.distance_miles == 1052.8

    # Alternate 2
    r3 = routes[2]
    assert r3.id == "r3"
    assert r3.label == "Alternative 2"
    assert r3.distance_miles == 1089.4


def test_valhalla_no_trip_error():
    provider = ValhallaProvider()
    with pytest.raises(NoRouteFoundError):
        provider._parse_response({"error": "No route found"})
