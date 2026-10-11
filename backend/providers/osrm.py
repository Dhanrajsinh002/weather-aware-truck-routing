"""OSRM routing provider adapter."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Sequence
import httpx

from backend.core.types import LatLng, Route
from backend.providers.base import NoRouteFoundError, RoutingError, RoutingProvider

logger = logging.getLogger(__name__)

DEFAULT_OSRM_URL = "https://router.project-osrm.org"
METERS_TO_MILES = 0.000621371
DEFAULT_TIMEOUT_SECONDS = 15.0


class OsrmProvider(RoutingProvider):
    """Adapter for OSRM public server."""

    def __init__(self, base_url: str = DEFAULT_OSRM_URL, timeout: float = DEFAULT_TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _parse_response(self, data: Dict[str, Any]) -> List[Route]:
        routes_data = data.get("routes", [])
        if not routes_data:
            raise NoRouteFoundError("No routes returned by OSRM")

        routes: List[Route] = []
        for idx, r in enumerate(routes_data):
            distance_meters = float(r.get("distance", 0.0))
            distance_miles = distance_meters * METERS_TO_MILES
            duration_seconds = float(r.get("duration", 0.0))

            geom = r.get("geometry", {})
            coords = geom.get("coordinates", [])

            label = "Fastest" if idx == 0 else f"Alternative {idx}"
            route_id = f"r{idx + 1}"

            routes.append(
                Route(
                    id=route_id,
                    label=label,
                    distance_miles=round(distance_miles, 1),
                    duration_seconds=round(duration_seconds, 1),
                    geometry=coords,
                )
            )

        return routes

    def get_routes(
        self,
        origin: LatLng,
        destination: LatLng,
        weight_lb: float = 0.0,
        via_waypoints: Sequence[LatLng] | None = None,
    ) -> List[Route]:
        """Fetch routes from OSRM, optionally via intermediate waypoints."""
        waypoints = [origin]
        if via_waypoints:
            waypoints.extend(via_waypoints)
        waypoints.append(destination)

        coord_str = ";".join(f"{pt.lng:.5f},{pt.lat:.5f}" for pt in waypoints)
        url = (
            f"{self.base_url}/route/v1/driving/{coord_str}"
            f"?overview=full&geometries=geojson&alternatives=3"
        )

        last_err: Exception | None = None
        for attempt in range(2):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    headers = {"User-Agent": "WeatherTruckRouting/1.0", "Accept": "application/json"}
                    resp = client.get(url, headers=headers)

                    if resp.status_code == 400:
                        raise NoRouteFoundError(f"OSRM invalid coordinate or unroutable: {resp.text}")
                    if resp.status_code >= 500:
                        raise RoutingError(f"OSRM server error: {resp.status_code}")

                    resp.raise_for_status()
                    data = resp.json()
                    return self._parse_response(data)

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                logger.warning("OSRM attempt %d failed: %s", attempt + 1, e)
                last_err = e
            except NoRouteFoundError:
                raise
            except Exception as e:
                logger.error("OSRM unexpected error: %s", e)
                raise RoutingError(f"OSRM routing failed: {e}") from e

        raise RoutingError(f"OSRM unavailable after retry: {last_err}")
