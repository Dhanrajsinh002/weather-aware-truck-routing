"""Valhalla routing provider adapter."""

from __future__ import annotations

import logging
from typing import Any, Dict, List
import httpx
import polyline

from backend.core.types import LatLng, Route
from backend.providers.base import NoRouteFoundError, RoutingError, RoutingProvider

logger = logging.getLogger(__name__)

DEFAULT_VALHALLA_URL = "https://valhalla1.openstreetmap.de/route"
LB_TO_METRIC_TONS = 0.000453592
DEFAULT_TIMEOUT_SECONDS = 15.0


class ValhallaProvider(RoutingProvider):
    """Adapter for Valhalla routing engine with truck costing."""

    def __init__(self, base_url: str = DEFAULT_VALHALLA_URL, timeout: float = DEFAULT_TIMEOUT_SECONDS):
        self.base_url = base_url
        self.timeout = timeout

    def _build_payload(self, origin: LatLng, destination: LatLng, weight_lb: float) -> Dict[str, Any]:
        weight_metric_tons = max(0.1, weight_lb * LB_TO_METRIC_TONS)
        return {
            "locations": [
                {"lat": origin.lat, "lon": origin.lng},
                {"lat": destination.lat, "lon": destination.lng},
            ],
            "costing": "truck",
            "costing_options": {
                "truck": {
                    "weight": round(weight_metric_tons, 2),
                }
            },
            "alternates": 2,
            "units": "miles",
            "directions_options": {"units": "miles"},
        }

    def _parse_response(self, data: Dict[str, Any]) -> List[Route]:
        trip = data.get("trip")
        if not trip:
            raise NoRouteFoundError(data.get("error", "No trip found in Valhalla response"))

        raw_trips = [trip]
        for alt in data.get("alternates", []):
            alt_trip = alt.get("trip") if isinstance(alt, dict) else None
            if alt_trip:
                raw_trips.append(alt_trip)

        routes: List[Route] = []
        for idx, t in enumerate(raw_trips):
            summary = t.get("summary", {})
            distance_miles = float(summary.get("length", 0.0))
            duration_seconds = float(summary.get("time", 0.0))

            coordinates: List[List[float]] = []
            legs = t.get("legs", [])
            for leg in legs:
                shape_str = leg.get("shape", "")
                if shape_str:
                    # Valhalla precision 6 polyline
                    decoded = polyline.decode(shape_str, precision=6)
                    # Convert (lat, lon) -> GeoJSON [lon, lat]
                    for lat, lon in decoded:
                        coordinates.append([round(lon, 5), round(lat, 5)])

            # De-duplicate adjacent identical vertices
            cleaned_coords: List[List[float]] = []
            for pt in coordinates:
                if not cleaned_coords or cleaned_coords[-1] != pt:
                    cleaned_coords.append(pt)

            label = "Fastest" if idx == 0 else f"Alternative {idx}"
            route_id = f"r{idx + 1}"

            routes.append(
                Route(
                    id=route_id,
                    label=label,
                    distance_miles=round(distance_miles, 1),
                    duration_seconds=round(duration_seconds, 1),
                    geometry=cleaned_coords,
                )
            )

        return routes

    def get_routes(self, origin: LatLng, destination: LatLng, weight_lb: float) -> List[Route]:
        """Fetch routes with 1 automatic retry on network timeout/failure."""
        payload = self._build_payload(origin, destination, weight_lb)
        last_err: Exception | None = None

        for attempt in range(2):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    headers = {"User-Agent": "WeatherTruckRouting/1.0", "Content-Type": "application/json"}
                    resp = client.post(self.base_url, json=payload, headers=headers)

                    if resp.status_code == 400:
                        raise NoRouteFoundError(f"Valhalla bad request: {resp.text}")
                    if resp.status_code >= 500:
                        raise RoutingError(f"Valhalla server error: {resp.status_code}")

                    resp.raise_for_status()
                    data = resp.json()
                    return self._parse_response(data)

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                logger.warning("Valhalla attempt %d failed: %s", attempt + 1, e)
                last_err = e
            except NoRouteFoundError:
                raise
            except Exception as e:
                logger.error("Valhalla unexpected error: %s", e)
                raise RoutingError(f"Valhalla routing failed: {e}") from e

        raise RoutingError(f"Valhalla unavailable after retry: {last_err}")
