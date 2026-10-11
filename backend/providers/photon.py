"""Photon geocoding provider adapter."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List
import httpx

from backend.providers.base import GeocodeError, GeocodeProvider, GeocodeResult

logger = logging.getLogger(__name__)

DEFAULT_PHOTON_URL = "https://photon.komoot.io/api"
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_USER_AGENT = os.environ.get(
    "USER_AGENT_CONTACT",
    "WeatherTruckRouting/1.0 (https://github.com/spotter-truck-routing; contact: support@example.com)",
)


def format_photon_label(props: Dict[str, Any]) -> str:
    """Format Photon feature properties into a clean display label."""
    parts: List[str] = []
    name = props.get("name")
    if name:
        parts.append(str(name))

    city = props.get("city")
    if city and city != name and city not in parts:
        parts.append(str(city))

    state = props.get("state")
    if state and state not in parts:
        parts.append(str(state))

    country = props.get("country")
    if country and country not in parts:
        parts.append(str(country))

    return ", ".join(parts) if parts else "Unknown Location"


class PhotonProvider(GeocodeProvider):
    """Adapter for Photon geocoding service."""

    def __init__(
        self,
        base_url: str = DEFAULT_PHOTON_URL,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        user_agent: str = DEFAULT_USER_AGENT,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.user_agent = user_agent
        self._cache: Dict[str, List[GeocodeResult]] = {}

    def _parse_response(self, data: Dict[str, Any]) -> List[GeocodeResult]:
        features = data.get("features", [])
        results: List[GeocodeResult] = []

        for feat in features:
            geom = feat.get("geometry", {})
            coords = geom.get("coordinates", [])
            if len(coords) < 2:
                continue
            lon, lat = coords[0], coords[1]
            props = feat.get("properties", {})
            label = format_photon_label(props)

            results.append(
                GeocodeResult(
                    label=label,
                    lat=round(float(lat), 5),
                    lng=round(float(lon), 5),
                )
            )

        return results

    def search(self, query: str, limit: int = 10) -> List[GeocodeResult]:
        """Search Photon for query string with custom User-Agent and query cache."""
        trimmed = query.strip()
        if not trimmed or len(trimmed) < 2:
            return []

        cache_key = trimmed.lower()
        if cache_key in self._cache:
            return self._cache[cache_key]

        params = {"q": trimmed, "limit": limit}
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(self.base_url, params=params, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                results = self._parse_response(data)
                self._cache[cache_key] = results
                return results
        except Exception as e:
            logger.warning("Photon geocode request failed: %s. Checking local fallback database.", e)
            # Check local fallback database if upstream has temporary issues
            matches = [
                GeocodeResult(label=item["label"], lat=item["lat"], lng=item["lng"])
                for item in MOCK_GEOCODE_FALLBACK
                if cache_key in item["label"].lower()
            ]
            if matches:
                return matches

            raise GeocodeError(f"Geocoding upstream failed: {e}") from e
