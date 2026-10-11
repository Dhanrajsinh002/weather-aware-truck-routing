"""Deterministic fixture weather provider simulating a winter storm along Chicago -> Denver."""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Sequence, Tuple

from backend.core.types import LatLng
from backend.core.weather_interp import HourlySeries
from backend.providers.base import WeatherProvider
from backend.providers.open_meteo import round_coord


class FixtureWeatherProvider(WeatherProvider):
    """Deterministic winter storm provider for reliable demos and offline testing."""

    def __init__(self, hours_ahead: int = 72):
        self.hours_ahead = hours_ahead

    def _generate_synthetic_hourly(
        self,
        lat: float,
        lng: float,
        start_time: datetime,
    ) -> HourlySeries:
        """Generate deterministic winter storm weather based on coordinate position.

        Progression from Chicago (-87.6) to Denver (-105.0):
        - -87.6 to -91.0 (IL): Low to Moderate (wind 18-28 mph, rain 0.1-0.2)
        - -91.0 to -96.0 (IA): Moderate to High (wind 32-38 mph, snow 0.8-1.5)
        - -96.0 to -102.0 (NE): Severe storm center (wind 46-56 mph, snow 2.0-3.5)
        - -102.0 to -105.0 (CO): High tapering to Moderate (wind 32-42 mph, snow 0.5-1.2)
        """
        times: List[datetime] = []
        winds: List[float] = []
        gusts: List[float] = []
        rains: List[float] = []
        snows: List[float] = []

        # Geographic storm peak around longitude -99.0 (central Nebraska)
        storm_center_lng = -99.0
        dist_from_center = abs(lng - storm_center_lng)

        # Base storm intensity (peaks at center)
        # Intensity factor from 0.0 (far away) to 1.0 (at center)
        intensity = max(0.0, 1.0 - (dist_from_center / 8.0))

        # Peak sustained wind ranges from 15 mph (calm) to 56 mph (No Travel)
        peak_wind = 15.0 + intensity * 41.0
        # Peak snowfall ranges from 0.0 to 3.2 in/hr
        peak_snow = intensity * 3.2
        # Peak rain near warmer eastern section
        is_east = lng > -93.0
        peak_rain = (0.25 * intensity) if is_east else 0.0

        for h in range(self.hours_ahead):
            t = start_time + timedelta(hours=h)
            times.append(t)

            # Storm movement/diurnal wave over time
            time_factor = math.sin((h + 6) * math.pi / 24.0) * 0.15 + 0.85
            current_wind = round(max(5.0, peak_wind * time_factor), 1)
            current_gust = round(current_wind * 1.3, 1)
            current_rain = round(max(0.0, peak_rain * time_factor), 2)
            current_snow = round(max(0.0, peak_snow * time_factor), 2)

            winds.append(current_wind)
            gusts.append(current_gust)
            rains.append(current_rain)
            snows.append(current_snow)

        return HourlySeries(
            times=times,
            wind_mph=winds,
            gust_mph=gusts,
            rain_in_hr=rains,
            snow_in_hr=snows,
        )

    def get_hourly_forecast(
        self,
        points: Sequence[LatLng],
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[Tuple[float, float], HourlySeries]:
        """Generate deterministic hourly forecast for all requested coordinates."""
        result: Dict[Tuple[float, float], HourlySeries] = {}
        for pt in points:
            grid_lat = round_coord(pt.lat)
            grid_lng = round_coord(pt.lng)
            key = (grid_lat, grid_lng)
            if key not in result:
                result[key] = self._generate_synthetic_hourly(grid_lat, grid_lng, start_time)
        return result
