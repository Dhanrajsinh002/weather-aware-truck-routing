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

# Comprehensive list of major US freight hubs and cities used for fallback & offline testing
MOCK_GEOCODE_FALLBACK: List[Dict[str, Any]] = [
    {"label": "Chicago, Illinois, USA", "lat": 41.8781, "lng": -87.6298},
    {"label": "Denver, Colorado, USA", "lat": 39.7392, "lng": -104.9903},
    {"label": "Raleigh, North Carolina, USA", "lat": 35.7796, "lng": -78.6382},
    {"label": "Rapid City, South Dakota, USA", "lat": 44.0805, "lng": -103.2310},
    {"label": "Grand Rapids, Michigan, USA", "lat": 42.9634, "lng": -85.6681},
    {"label": "Omaha, Nebraska, USA", "lat": 41.2565, "lng": -95.9345},
    {"label": "Des Moines, Iowa, USA", "lat": 41.6005, "lng": -93.6091},
    {"label": "Lincoln, Nebraska, USA", "lat": 40.8136, "lng": -96.7026},
    {"label": "Kansas City, Missouri, USA", "lat": 39.0997, "lng": -94.5786},
    {"label": "Cheyenne, Wyoming, USA", "lat": 41.1399, "lng": -104.8202},
    {"label": "Dallas, Texas, USA", "lat": 32.7767, "lng": -96.7970},
    {"label": "Minneapolis, Minnesota, USA", "lat": 44.9778, "lng": -93.2650},
    {"label": "Salt Lake City, Utah, USA", "lat": 40.7608, "lng": -111.8910},
    {"label": "Atlanta, Georgia, USA", "lat": 33.7490, "lng": -84.3880},
    {"label": "Indianapolis, Indiana, USA", "lat": 39.7684, "lng": -86.1581},
    {"label": "St. Louis, Missouri, USA", "lat": 38.6270, "lng": -90.1994},
    {"label": "Nashville, Tennessee, USA", "lat": 36.1627, "lng": -86.7816},
    {"label": "Memphis, Tennessee, USA", "lat": 35.1495, "lng": -90.0490},
    {"label": "Columbus, Ohio, USA", "lat": 39.9612, "lng": -82.9988},
    {"label": "Cleveland, Ohio, USA", "lat": 41.4993, "lng": -81.6944},
    {"label": "Detroit, Michigan, USA", "lat": 42.3314, "lng": -83.0458},
    {"label": "Pittsburgh, Pennsylvania, USA", "lat": 40.4406, "lng": -79.9959},
    {"label": "Philadelphia, Pennsylvania, USA", "lat": 39.9526, "lng": -75.1652},
    {"label": "New York, New York, USA", "lat": 40.7128, "lng": -74.0060},
    {"label": "Boston, Massachusetts, USA", "lat": 42.3601, "lng": -71.0589},
    {"label": "Seattle, Washington, USA", "lat": 47.6062, "lng": -122.3321},
    {"label": "Portland, Oregon, USA", "lat": 45.5152, "lng": -122.6784},
    {"label": "Los Angeles, California, USA", "lat": 34.0522, "lng": -118.2437},
    {"label": "San Francisco, California, USA", "lat": 37.7749, "lng": -122.4194},
    {"label": "Phoenix, Arizona, USA", "lat": 33.4484, "lng": -112.0740},
    {"label": "Houston, Texas, USA", "lat": 29.7604, "lng": -95.3698},
    {"label": "San Antonio, Texas, USA", "lat": 29.4241, "lng": -98.4936},
    {"label": "Austin, Texas, USA", "lat": 30.2672, "lng": -97.7431},
    {"label": "El Paso, Texas, USA", "lat": 31.7619, "lng": -106.4850},
    {"label": "Albuquerque, New Mexico, USA", "lat": 35.0844, "lng": -106.6504},
    {"label": "Charlotte, North Carolina, USA", "lat": 35.2271, "lng": -80.8431},
    {"label": "Tampa, Florida, USA", "lat": 27.9506, "lng": -82.4572},
    {"label": "Miami, Florida, USA", "lat": 25.7617, "lng": -80.1918},
    {"label": "Orlando, Florida, USA", "lat": 28.5383, "lng": -81.3792},
    {"label": "Jacksonville, Florida, USA", "lat": 30.3322, "lng": -81.6557},
    {"label": "New Orleans, Louisiana, USA", "lat": 29.9511, "lng": -90.0715},
    {"label": "Oklahoma City, Oklahoma, USA", "lat": 35.4676, "lng": -97.5164},
    {"label": "Tulsa, Oklahoma, USA", "lat": 36.1540, "lng": -95.9928},
    {"label": "Wichita, Kansas, USA", "lat": 37.6872, "lng": -97.3301},
    {"label": "Milwaukee, Wisconsin, USA", "lat": 43.0389, "lng": -87.9065},
    {"label": "Louisville, Kentucky, USA", "lat": 38.2527, "lng": -85.7585},
    {"label": "Cincinnati, Ohio, USA", "lat": 39.1031, "lng": -84.5120},
    {"label": "Fargo, North Dakota, USA", "lat": 46.8772, "lng": -96.7898},
    {"label": "Billings, Montana, USA", "lat": 45.7833, "lng": -108.5007},
    {"label": "Boise, Idaho, USA", "lat": 43.6150, "lng": -116.2023},
    {"label": "Sacramento, California, USA", "lat": 38.5816, "lng": -121.4944},
    {"tag": "San Diego", "label": "San Diego, California, USA", "lat": 32.7157, "lng": -117.1611},
    {"label": "Las Vegas, Nevada, USA", "lat": 36.1699, "lng": -115.1398},
    {"label": "Reno, Nevada, USA", "lat": 39.5296, "lng": -119.8138},
]


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
                self._cache[cache_key] = matches[:limit]
                return matches[:limit]

            return []

