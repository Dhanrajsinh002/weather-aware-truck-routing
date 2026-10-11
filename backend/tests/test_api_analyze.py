import os
from datetime import datetime, timezone, timedelta
import pytest
from rest_framework.test import APIClient
from backend.core.types import LatLng, Route
from backend.providers.base import NoRouteFoundError, WeatherServiceError
from backend.providers.fixture_weather import FixtureWeatherProvider


@pytest.fixture(autouse=True)
def setup_django_env():
    os.environ["DJANGO_SETTINGS_MODULE"] = "backend.config.settings"


@pytest.fixture
def api_client():
    return APIClient()


def test_health_endpoint(api_client):
    resp = api_client.get("/api/health/")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_geocode_short_query(api_client):
    resp = api_client.get("/api/geocode/?q=a")
    assert resp.status_code == 200
    assert resp.json() == {"results": []}


def test_geocode_mocked_results(api_client, monkeypatch):
    from backend.api import views
    class MockPhoton:
        def search(self, q):
            from backend.providers.base import GeocodeResult
            return [GeocodeResult(label="Chicago, IL", lat=41.8781, lng=-87.6298)]

    monkeypatch.setattr(views, "geocode_provider", MockPhoton())
    resp = api_client.get("/api/geocode/?q=Chicago")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["label"] == "Chicago, IL"


def test_analyze_validation_errors(api_client):
    # Invalid weight (0 lb)
    payload_bad_weight = {
        "origin": {"lat": 41.88, "lng": -87.63, "label": "Chicago"},
        "destination": {"lat": 39.74, "lng": -104.99, "label": "Denver"},
        "departure_time": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
        "load_weight_lb": 0,
        "checkpoint_interval_miles": "auto",
    }
    resp = api_client.post("/api/analyze/", payload_bad_weight, format="json")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "VALIDATION"
    assert "load_weight_lb" in resp.json()["error"]["fields"]

    # Departure time in past (> 1 hour)
    payload_past = dict(payload_bad_weight)
    payload_past["load_weight_lb"] = 40000
    payload_past["departure_time"] = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
    resp_past = api_client.post("/api/analyze/", payload_past, format="json")
    assert resp_past.status_code == 400
    assert "departure_time" in resp_past.json()["error"]["fields"]


def test_analyze_end_to_end_fixture_mode(api_client, monkeypatch):
    from backend.api import views
    from backend.services.routes import RouteService

    # Mock RouteService to return deterministic synthetic routes
    class MockRouteService:
        def get_diverse_routes(self, origin, destination, weight_lb):
            # Synthetic Chicago -> Denver line
            coords1 = [[-87.63, 41.88], [-95.93, 41.25], [-104.99, 39.74]]
            coords2 = [[-87.63, 41.88], [-94.58, 39.10], [-104.99, 39.74]]
            coords3 = [[-87.63, 41.88], [-104.82, 41.14], [-104.99, 39.74]]
            return [
                Route(id="r1", label="Fastest", distance_miles=1003.2, duration_seconds=54000.0, geometry=coords1),
                Route(id="r2", label="Alternative 1", distance_miles=1052.8, duration_seconds=57600.0, geometry=coords2),
                Route(id="r3", label="Alternative 2", distance_miles=1089.4, duration_seconds=59400.0, geometry=coords3),
            ]

    analyze_svc = views.AnalyzeService(
        route_service=MockRouteService(),
        weather_provider=FixtureWeatherProvider(),
    )
    monkeypatch.setattr(views, "analyze_service", analyze_svc)

    dep_time = (datetime.now(timezone.utc) + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "origin": {"lat": 41.8781, "lng": -87.6298, "label": "Chicago, IL"},
        "destination": {"lat": 39.7392, "lng": -104.9903, "label": "Denver, CO"},
        "departure_time": dep_time,
        "load_weight_lb": 42000,
        "checkpoint_interval_miles": 25,
    }

    resp = api_client.post("/api/analyze/", payload, format="json")
    assert resp.status_code == 200
    data = resp.json()

    # Validate top-level contract fields
    assert "request_id" in data
    assert data["interval_miles"] == 25
    assert len(data["routes"]) == 3
    assert "recommendation" in data
    assert "heatmap" in data

    # Validate route structure
    r1 = data["routes"][0]
    assert r1["id"] in ("r1", "r2", "r3")
    assert "distance_miles" in r1
    assert "duration_seconds" in r1
    assert r1["geometry"]["type"] == "LineString"
    assert len(r1["geometry"]["coordinates"]) > 0
    assert "metrics" in r1
    assert "checkpoints" in r1
    assert len(r1["checkpoints"]) > 0

    # Validate checkpoint structure
    cp0 = r1["checkpoints"][0]
    assert "index" in cp0
    assert "mile" in cp0
    assert "eta" in cp0
    assert "weather" in cp0
    assert "wind_mph" in cp0["weather"]
    assert "risk" in cp0
    assert "level" in cp0["risk"]
    assert "score" in cp0["risk"]
    assert "drivers" in cp0["risk"]

    # Validate recommendation structure
    rec = data["recommendation"]
    assert "route_id" in rec
    assert isinstance(rec["reasons"], list)
    assert len(rec["reasons"]) > 0

    # Validate heatmap structure
    hm = data["heatmap"]
    assert hm["hours"] == 49
    assert len(hm["points"]) > 0
    assert len(hm["points"][0]["levels"]) == 49


def test_analyze_no_route_error(api_client, monkeypatch):
    from backend.api import views

    class FailingRouteService:
        def get_diverse_routes(self, o, d, w):
            raise NoRouteFoundError("No truck path across water")

    analyze_svc = views.AnalyzeService(route_service=FailingRouteService())
    monkeypatch.setattr(views, "analyze_service", analyze_svc)

    dep_time = (datetime.now(timezone.utc) + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "origin": {"lat": 41.88, "lng": -87.63, "label": "Chicago"},
        "destination": {"lat": 39.74, "lng": -104.99, "label": "Denver"},
        "departure_time": dep_time,
        "load_weight_lb": 35000,
        "checkpoint_interval_miles": "auto",
    }

    resp = api_client.post("/api/analyze/", payload, format="json")
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "NO_ROUTE"


def test_analyze_weather_service_error(api_client, monkeypatch):
    from backend.api import views

    class MockRouteService:
        def get_diverse_routes(self, o, d, w):
            return [Route(id="r1", label="Fastest", distance_miles=100.0, duration_seconds=3600.0, geometry=[[-87.6, 41.8], [-88.0, 42.0]])]

    class FailingWeather:
        def get_hourly_forecast(self, p, s, e):
            raise WeatherServiceError("Open-Meteo gateway timeout")

    analyze_svc = views.AnalyzeService(
        route_service=MockRouteService(),
        weather_provider=FailingWeather(),
    )
    monkeypatch.setattr(views, "analyze_service", analyze_svc)

    dep_time = (datetime.now(timezone.utc) + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "origin": {"lat": 41.88, "lng": -87.63, "label": "Chicago"},
        "destination": {"lat": 39.74, "lng": -104.99, "label": "Denver"},
        "departure_time": dep_time,
        "load_weight_lb": 35000,
        "checkpoint_interval_miles": 25,
    }

    resp = api_client.post("/api/analyze/", payload, format="json")
    assert resp.status_code == 502
    assert resp.json()["error"]["code"] == "UPSTREAM"
    assert resp.json()["error"]["provider"] == "weather"
