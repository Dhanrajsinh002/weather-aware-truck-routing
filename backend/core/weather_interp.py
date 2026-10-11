"""Linear weather interpolation across hourly forecast series.

Pure Python, no external libraries, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Tuple
from backend.core.types import Weather


@dataclass
class HourlySeries:
    """Hourly forecast series for a geographic coordinate."""

    times: List[datetime] = field(default_factory=list)
    wind_mph: List[float] = field(default_factory=list)
    gust_mph: List[float] = field(default_factory=list)
    rain_in_hr: List[float] = field(default_factory=list)
    snow_in_hr: List[float] = field(default_factory=list)


def interpolate_weather_at_time(
    series: HourlySeries,
    target_time: datetime,
) -> Tuple[Weather, bool]:
    """Interpolate weather values at target_time from an hourly forecast series.

    Returns:
    (Weather, forecast_unavailable: bool)
    """
    if not series.times or not series.wind_mph:
        return Weather(), True

    n = len(series.times)
    first_time = series.times[0]
    last_time = series.times[-1]

    # Target is before the available forecast horizon
    if target_time < first_time:
        w = Weather(
            wind_mph=series.wind_mph[0],
            gust_mph=series.gust_mph[0] if series.gust_mph else 0.0,
            rain_in_hr=series.rain_in_hr[0] if series.rain_in_hr else 0.0,
            snow_in_hr=series.snow_in_hr[0] if series.snow_in_hr else 0.0,
        )
        return w, True

    # Target is beyond the available forecast horizon
    if target_time > last_time:
        w = Weather(
            wind_mph=series.wind_mph[-1],
            gust_mph=series.gust_mph[-1] if series.gust_mph else 0.0,
            rain_in_hr=series.rain_in_hr[-1] if series.rain_in_hr else 0.0,
            snow_in_hr=series.snow_in_hr[-1] if series.snow_in_hr else 0.0,
        )
        return w, True

    # Search for bracketing hour
    for i in range(n - 1):
        t_start = series.times[i]
        t_end = series.times[i + 1]

        if t_start <= target_time <= t_end:
            total_sec = (t_end - t_start).total_seconds()
            if total_sec <= 0:
                fraction = 0.0
            else:
                fraction = (target_time - t_start).total_seconds() / total_sec

            wind = series.wind_mph[i] + fraction * (series.wind_mph[i + 1] - series.wind_mph[i])
            gust = (
                (series.gust_mph[i] + fraction * (series.gust_mph[i + 1] - series.gust_mph[i]))
                if series.gust_mph
                else 0.0
            )
            rain = (
                (series.rain_in_hr[i] + fraction * (series.rain_in_hr[i + 1] - series.rain_in_hr[i]))
                if series.rain_in_hr
                else 0.0
            )
            snow = (
                (series.snow_in_hr[i] + fraction * (series.snow_in_hr[i + 1] - series.snow_in_hr[i]))
                if series.snow_in_hr
                else 0.0
            )

            return (
                Weather(
                    wind_mph=round(max(0.0, wind), 2),
                    gust_mph=round(max(0.0, gust), 2),
                    rain_in_hr=round(max(0.0, rain), 3),
                    snow_in_hr=round(max(0.0, snow), 3),
                ),
                False,
            )

    # Exact match on last item
    return (
        Weather(
            wind_mph=series.wind_mph[-1],
            gust_mph=series.gust_mph[-1] if series.gust_mph else 0.0,
            rain_in_hr=series.rain_in_hr[-1] if series.rain_in_hr else 0.0,
            snow_in_hr=series.snow_in_hr[-1] if series.snow_in_hr else 0.0,
        ),
        False,
    )
