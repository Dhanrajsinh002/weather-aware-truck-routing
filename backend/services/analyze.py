"""Trip analysis service orchestrating routes, checkpoints, weather, risk, and heatmap."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
import os
import uuid
from typing import Any, Dict, List, Tuple
from backend.core.eta import compute_checkpoints_eta
from backend.core.heatmap import build_corridor_heatmap, sample_corridor_points
from backend.core.metrics import compute_route_metrics, compute_segment_ownership
from backend.core.recommend import rank_and_recommend_routes
from backend.core.risk import classify_checkpoint
from backend.core.sampling import auto_interval, sample_checkpoints
from backend.core.types import LatLng, RiskLevel, Route
from backend.core.weather_interp import HourlySeries, interpolate_weather_at_time
from backend.providers.base import NoRouteFoundError, WeatherProvider
from backend.providers.fixture_weather import FixtureWeatherProvider
from backend.providers.open_meteo import OpenMeteoProvider, round_coord
from backend.services.routes import RouteService

logger = logging.getLogger(__name__)


def validate_trip_request(
    load_weight_lb: float,
    departure_time: datetime,
) -> Dict[str, str]:
    """Validate load weight and departure time.

    Returns dict of field errors (empty if valid).
    """
    errors: Dict[str, str] = {}

    # Weight limits: 1 to 100,000 lb
    if load_weight_lb < 1.0 or load_weight_lb > 100000.0:
        errors["load_weight_lb"] = "Load weight must be between 1 and 100,000 lbs."

    now = datetime.now(timezone.utc)
    # Departure validation: not more than 1 h in past, not more than 14 days ahead
    if departure_time < (now - timedelta(hours=1, minutes=5)):
        errors["departure_time"] = "Departure time cannot be more than 1 hour in the past."
    elif departure_time > (now + timedelta(days=14)):
        errors["departure_time"] = "Departure time cannot be more than 14 days in the future."

    return errors


class AnalyzeService:
    """Service that coordinates routing, sampling, weather forecasts, and risk evaluation."""

    def __init__(
        self,
        route_service: RouteService | None = None,
        weather_provider: WeatherProvider | None = None,
    ):
        self.route_service = route_service or RouteService()
        self.weather_provider = weather_provider

    def _get_weather_provider(self, mode: str) -> WeatherProvider:
        if self.weather_provider is not None:
            return self.weather_provider
        if mode == "fixture":
            return FixtureWeatherProvider()
        return OpenMeteoProvider()

    def analyze_trip(
        self,
        origin: LatLng,
        destination: LatLng,
        departure_time: datetime,
        load_weight_lb: float,
        checkpoint_interval_miles: Any,
        weather_mode: str | None = None,
    ) -> Dict[str, Any]:
        """Perform end-to-end trip analysis."""
        mode = (weather_mode or os.environ.get("WEATHER_MODE", "live")).lower()
        provider = self._get_weather_provider(mode)

        # 1. Fetch routes
        routes = self.route_service.get_diverse_routes(origin, destination, load_weight_lb)

        if not routes:
            raise NoRouteFoundError(
                "No viable driving route could be found between the selected locations. Please check your origin and destination."
            )

        # 2. Determine sampling interval
        chosen_interval: int
        if isinstance(checkpoint_interval_miles, int) and checkpoint_interval_miles in (10, 25, 50):
            chosen_interval = checkpoint_interval_miles
        else:
            # Auto interval based on primary route distance
            chosen_interval = auto_interval(routes[0].distance_miles)

        # 3. Sample checkpoints & compute ETAs for each route
        all_weather_points: List[LatLng] = []
        route_geometries = [r.geometry for r in routes]

        for route in routes:
            # Sample checkpoints along geometry
            cps = sample_checkpoints(route.geometry, float(chosen_interval), default_eta=departure_time)
            # Compute monotonic ETAs
            cps = compute_checkpoints_eta(cps, route.distance_miles, route.duration_seconds, departure_time)
            route.checkpoints = cps
            for cp in cps:
                all_weather_points.append(LatLng(lat=cp.lat, lng=cp.lng))

        # 4. Heatmap corridor sampling points
        corridor_points = sample_corridor_points(route_geometries, spacing_miles=10.0)
        all_weather_points.extend(corridor_points)

        # 5. Single batched weather fetch for checkpoints + heatmap corridor
        # Max horizon: 49 hours after departure or destination arrival
        max_duration = max(r.duration_seconds for r in routes)
        end_time = departure_time + timedelta(seconds=max(max_duration, 49 * 3600.0))

        weather_lookup = provider.get_hourly_forecast(all_weather_points, departure_time, end_time)

        # 6. Evaluate risk per checkpoint
        fallback_series = HourlySeries()
        forecast_unavailable_any = False

        for route in routes:
            for cp in route.checkpoints:
                grid_key = (round_coord(cp.lat), round_coord(cp.lng))
                series = weather_lookup.get(grid_key, fallback_series)
                weather, unavailable = interpolate_weather_at_time(series, cp.eta)
                if unavailable:
                    forecast_unavailable_any = True

                risk = classify_checkpoint(weather, load_weight_lb)
                cp.weather = weather
                cp.risk = risk

            # 7. Segment ownership & route metrics
            compute_segment_ownership(route.checkpoints, route.distance_miles)
            route.metrics = compute_route_metrics(route.checkpoints, route.distance_miles)

        # 8. Rank and recommend
        ranked_routes, recommendation = rank_and_recommend_routes(routes)

        if forecast_unavailable_any:
            recommendation.warnings.append(
                "Some checkpoints extend beyond the reliable forecast window; estimates clamped to nearest available."
            )

        # 9. Build 49-hour corridor heatmap
        heatmap_points = build_corridor_heatmap(
            route_geometries=route_geometries,
            weather_lookup=weather_lookup,
            departure_time=departure_time,
            load_lb=load_weight_lb,
            spacing_miles=10.0,
            hours=49,
        )

        # 10. Format final response payload exactly per api-contract
        return {
            "request_id": str(uuid.uuid4()),
            "weather_mode": mode,
            "interval_miles": chosen_interval,
            "routes": [
                {
                    "id": r.id,
                    "label": r.label,
                    "distance_miles": r.distance_miles,
                    "duration_seconds": int(r.duration_seconds),
                    "geometry": {
                        "type": "LineString",
                        "coordinates": r.geometry,
                    },
                    "metrics": {
                        "no_travel_miles": r.metrics.no_travel_miles if r.metrics else 0.0,
                        "severe_miles": r.metrics.severe_miles if r.metrics else 0.0,
                        "high_miles": r.metrics.high_miles if r.metrics else 0.0,
                        "avg_risk": r.metrics.avg_risk if r.metrics else 0.0,
                        "max_level": r.metrics.max_level.name if r.metrics else "LOW",
                    },
                    "checkpoints": [
                        {
                            "index": cp.index,
                            "mile": cp.mile,
                            "lat": cp.lat,
                            "lng": cp.lng,
                            "eta": cp.eta.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "weather": {
                                "wind_mph": cp.weather.wind_mph if cp.weather else 0.0,
                                "gust_mph": cp.weather.gust_mph if cp.weather else 0.0,
                                "rain_in_hr": cp.weather.rain_in_hr if cp.weather else 0.0,
                                "snow_in_hr": cp.weather.snow_in_hr if cp.weather else 0.0,
                            },
                            "risk": {
                                "level": cp.risk.level.name if cp.risk else "LOW",
                                "score": cp.risk.score if cp.risk else 0,
                                "drivers": cp.risk.drivers if cp.risk else [],
                            },
                        }
                        for cp in r.checkpoints
                    ],
                    "rank": r.rank,
                    "recommended": r.recommended,
                }
                for r in ranked_routes
            ],
            "recommendation": {
                "route_id": recommendation.route_id,
                "reasons": recommendation.reasons,
                "warnings": recommendation.warnings,
            },
            "heatmap": {
                "start_time": departure_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "hours": 49,
                "points": [
                    {
                        "lat": hp.lat,
                        "lng": hp.lng,
                        "levels": hp.levels,
                    }
                    for hp in heatmap_points
                ],
            },
        }
