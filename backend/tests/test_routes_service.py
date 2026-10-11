import json
from pathlib import Path
import pytest
from backend.core.types import LatLng, Route
from backend.providers.base import RoutingError
from backend.providers.osrm import OsrmProvider
from backend.services.routes import (
    RouteService,
    compute_geometry_overlap,
    deduplicate_routes,
    relabel_and_index_routes,
)


def test_parse_osrm_fixture():
    fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "osrm_chicago_denver.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    provider = OsrmProvider()
    routes = provider._parse_response(data)

    assert len(routes) == 2
    assert routes[0].id == "r1"
    assert routes[0].label == "Fastest"
    assert pytest.approx(routes[0].distance_miles, abs=1.0) == 1003.2
    assert routes[0].duration_seconds == 54000.0


def test_compute_geometry_overlap_identical():
    coords = [[-87.6, 41.8], [-95.9, 41.2], [-104.9, 39.7]]
    overlap = compute_geometry_overlap(coords, coords)
    assert overlap >= 0.99


def test_compute_geometry_overlap_disjoint():
    coords_a = [[-87.6, 41.8], [-95.9, 41.2]]
    coords_b = [[-70.0, 30.0], [-71.0, 31.0]]
    overlap = compute_geometry_overlap(coords_a, coords_b)
    assert overlap == 0.0


def test_route_service_fallback_when_primary_fails():
    class FailingValhalla:
        def get_routes(self, origin, destination, weight_lb):
            raise RoutingError("Valhalla 502")

    class WorkingOsrm:
        def get_routes(self, origin, destination, weight_lb, via_waypoints=None):
            return [
                Route(
                    id="tmp1",
                    label="",
                    distance_miles=1000.0,
                    duration_seconds=50000.0,
                    geometry=[[-87.6, 41.8], [-104.9, 39.7]],
                )
            ]

    service = RouteService(primary_provider=FailingValhalla(), fallback_provider=WorkingOsrm())
    routes = service.get_diverse_routes(LatLng(41.88, -87.63), LatLng(39.74, -104.99), 40000.0)

    assert len(routes) >= 1
    assert routes[0].id == "r1"
    assert routes[0].label == "Fastest"


def test_relabel_and_index_routes():
    r1 = Route(id="a", label="foo", distance_miles=100, duration_seconds=60000)
    r2 = Route(id="b", label="bar", distance_miles=100, duration_seconds=40000)
    relabeled = relabel_and_index_routes([r1, r2])

    assert relabeled[0].id == "r1"
    assert relabeled[0].label == "Fastest"
    assert relabeled[0].duration_seconds == 40000

    assert relabeled[1].id == "r2"
    assert relabeled[1].label == "Alternative 1"
    assert relabeled[1].duration_seconds == 60000
