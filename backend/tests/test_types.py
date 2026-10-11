import pytest
from datetime import datetime, timezone
from backend.core.types import (
    RiskLevel,
    LatLng,
    Weather,
    RiskResult,
    Checkpoint,
    RouteMetrics,
    Route,
    HeatmapPoint,
    Recommendation,
)


def test_risk_level_values():
    assert RiskLevel.LOW == 0
    assert RiskLevel.MODERATE == 1
    assert RiskLevel.HIGH == 2
    assert RiskLevel.SEVERE == 3
    assert RiskLevel.NO_TRAVEL == 4
    assert RiskLevel.LOW < RiskLevel.MODERATE < RiskLevel.HIGH < RiskLevel.SEVERE < RiskLevel.NO_TRAVEL
    assert RiskLevel.LOW.name == "LOW"
    assert RiskLevel.NO_TRAVEL.name == "NO_TRAVEL"


def test_lat_lng():
    pt = LatLng(lat=41.8781, lng=-87.6298)
    assert pt.lat == 41.8781
    assert pt.lng == -87.6298


def test_weather():
    w = Weather(wind_mph=20.5, gust_mph=28.0, rain_in_hr=0.15, snow_in_hr=0.0)
    assert w.wind_mph == 20.5
    assert w.gust_mph == 28.0
    assert w.rain_in_hr == 0.15
    assert w.snow_in_hr == 0.0


def test_checkpoint_and_risk_result():
    risk = RiskResult(level=RiskLevel.SEVERE, score=3, drivers=["Wind 48 mph + load 35,000 lb -> No Travel"])
    now = datetime.now(timezone.utc)
    cp = Checkpoint(
        index=0,
        mile=0.0,
        lat=41.88,
        lng=-87.63,
        eta=now,
        weather=Weather(wind_mph=10.0),
        risk=risk,
        owned_miles=12.5,
    )
    assert cp.index == 0
    assert cp.mile == 0.0
    assert cp.risk.level == RiskLevel.SEVERE
    assert cp.owned_miles == 12.5


def test_route_metrics():
    metrics = RouteMetrics(
        no_travel_miles=0.0,
        severe_miles=12.5,
        high_miles=40.0,
        avg_risk=0.84,
        max_level=RiskLevel.SEVERE,
    )
    assert metrics.no_travel_miles == 0.0
    assert metrics.severe_miles == 12.5
    assert metrics.max_level == RiskLevel.SEVERE


def test_route_and_recommendation():
    route = Route(
        id="r1",
        label="Fastest",
        distance_miles=1003.2,
        duration_seconds=54000.0,
        geometry=[[-87.6, 41.8], [-88.0, 42.0]],
    )
    assert route.id == "r1"
    assert route.recommended is False
    rec = Recommendation(
        route_id="r1",
        reasons=["Fewest Severe miles"],
        warnings=[],
    )
    assert rec.route_id == "r1"
