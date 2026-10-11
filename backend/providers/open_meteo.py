"""Open-Meteo hourly weather forecast provider."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import logging
import time
from typing import Any, Dict, List, Sequence, Tuple
import httpx

from backend.core.types import LatLng
from backend.core.weather_interp import HourlySeries
from backend.providers.base import WeatherProvider, WeatherServiceError

logger = logging.getLogger(__name__)

DEFAULT_OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
BATCH_SIZE = 50
CACHE_TTL_SECONDS = 1800  # 30 minutes


def round_coord(val: float) -> float:
    return round(val, 1)


class InMemoryCache:
    """Simple in-memory TTL cache fallback when Django cache is not initialized."""

    def __init__(self):
        self._store: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        if key in self._store:
            exp, val = self._store[key]
            if time.time() < exp:
                return val
            del self._store[key]
        return None

    def set(self, key: str, val: Any, timeout: int = CACHE_TTL_SECONDS):
        self._store[key] = (time.time() + timeout, val)


_memory_cache = InMemoryCache()


def get_cache_client():
    """Return Django cache if settings are configured; otherwise return InMemoryCache."""
    try:
        from django.conf import settings
        if settings.configured:
            from django.core.cache import cache
            return cache
    except Exception:
        pass
    return _memory_cache


class OpenMeteoProvider(WeatherProvider):
    """Adapter for Open-Meteo multi-point hourly weather forecast."""

    def __init__(
        self,
        base_url: str = DEFAULT_OPEN_METEO_URL,
        timeout: float = 15.0,
        max_workers: int = 5,
        cache_client: Any | None = None,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.max_workers = max_workers
        self.cache_client = cache_client

    def _get_cache(self):
        return self.cache_client or get_cache_client()

    def _parse_hourly_data(self, item: Dict[str, Any]) -> HourlySeries:
        hourly = item.get("hourly", {})
        raw_times = hourly.get("time", [])
        winds = hourly.get("wind_speed_10m", [])
        gusts = hourly.get("wind_gusts_10m", [])
        rains = hourly.get("rain", [])
        showers = hourly.get("showers", [])
        snows = hourly.get("snowfall", [])

        times: List[datetime] = []
        parsed_winds: List[float] = []
        parsed_gusts: List[float] = []
        parsed_rains: List[float] = []
        parsed_snows: List[float] = []

        for idx, t_str in enumerate(raw_times):
            # Format: 2026-10-12T14:00
            try:
                dt = datetime.fromisoformat(t_str)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
            except Exception:
                continue

            times.append(dt)
            w = float(winds[idx]) if idx < len(winds) and winds[idx] is not None else 0.0
            g = float(gusts[idx]) if idx < len(gusts) and gusts[idx] is not None else w
            r = float(rains[idx]) if idx < len(rains) and rains[idx] is not None else 0.0
            sh = float(showers[idx]) if idx < len(showers) and showers[idx] is not None else 0.0
            sn = float(snows[idx]) if idx < len(snows) and snows[idx] is not None else 0.0

            parsed_winds.append(round(w, 2))
            parsed_gusts.append(round(g, 2))
            parsed_rains.append(round(r + sh, 3))  # rain = rain + showers
            parsed_snows.append(round(sn, 3))

        return HourlySeries(
            times=times,
            wind_mph=parsed_winds,
            gust_mph=parsed_gusts,
            rain_in_hr=parsed_rains,
            snow_in_hr=parsed_snows,
        )

    def _fetch_batch(
        self,
        batch_coords: List[Tuple[float, float]],
        start_date: str,
        end_date: str,
    ) -> Dict[Tuple[float, float], HourlySeries]:
        """Fetch weather for a batch of <= 50 coordinates with backoff on 429/5xx."""
        lat_str = ",".join(str(c[0]) for c in batch_coords)
        lon_str = ",".join(str(c[1]) for c in batch_coords)

        params = {
            "latitude": lat_str,
            "longitude": lon_str,
            "hourly": "wind_speed_10m,wind_gusts_10m,rain,showers,snowfall",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "timezone": "GMT",
            "start_date": start_date,
            "end_date": end_date,
        }

        retries = 3
        backoff = 0.5
        last_exc: Exception | None = None

        for attempt in range(retries):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.get(self.base_url, params=params)

                    if resp.status_code in (429, 500, 502, 503, 504):
                        logger.warning(
                            "Open-Meteo status %d on attempt %d. Backing off for %.2fs",
                            resp.status_code,
                            attempt + 1,
                            backoff,
                        )
                        time.sleep(backoff)
                        backoff *= 2.0
                        continue

                    resp.raise_for_status()
                    data = resp.json()

                    # Single location returns a dict, multi-location returns a list
                    items = data if isinstance(data, list) else [data]

                    result: Dict[Tuple[float, float], HourlySeries] = {}
                    for idx, item in enumerate(items):
                        if idx < len(batch_coords):
                            coord = batch_coords[idx]
                            series = self._parse_hourly_data(item)
                            result[coord] = series
                    return result

            except Exception as e:
                logger.warning("Open-Meteo batch request error: %s", e)
                last_exc = e
                time.sleep(backoff)
                backoff *= 2.0

        raise WeatherServiceError(f"Open-Meteo failed after retries: {last_exc}")

    def get_hourly_forecast(
        self,
        points: Sequence[LatLng],
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[Tuple[float, float], HourlySeries]:
        """Fetch forecasts with deduplication on 0.1° grid, caching, and parallel batching."""
        if not points:
            return {}

        start_date = start_time.strftime("%Y-%m-%d")
        end_date = end_time.strftime("%Y-%m-%d")

        # 1. Deduplicate points to 0.1 deg
        unique_coords: List[Tuple[float, float]] = []
        seen = set()
        for pt in points:
            cell = (round_coord(pt.lat), round_coord(pt.lng))
            if cell not in seen:
                seen.add(cell)
                unique_coords.append(cell)

        # 2. Check cache
        cache = self._get_cache()
        final_result: Dict[Tuple[float, float], HourlySeries] = {}
        missing_coords: List[Tuple[float, float]] = []

        for coord in unique_coords:
            cache_key = f"weather:{coord[0]}:{coord[1]}:{start_date}:{end_date}"
            cached_val = cache.get(cache_key)
            if cached_val is not None:
                final_result[coord] = cached_val
            else:
                missing_coords.append(coord)

        if not missing_coords:
            return final_result

        # 3. Batch missing coordinates
        batches = [
            missing_coords[i : i + BATCH_SIZE]
            for i in range(0, len(missing_coords), BATCH_SIZE)
        ]

        # 4. Fetch in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_batch = {
                executor.submit(self._fetch_batch, b, start_date, end_date): b
                for b in batches
            }

            for future in as_completed(future_to_batch):
                batch_data = future.result()
                for coord, series in batch_data.items():
                    final_result[coord] = series
                    cache_key = f"weather:{coord[0]}:{coord[1]}:{start_date}:{end_date}"
                    cache.set(cache_key, series, timeout=CACHE_TTL_SECONDS)

        return final_result
