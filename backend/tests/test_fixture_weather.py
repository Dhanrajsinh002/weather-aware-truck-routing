from datetime import datetime, timezone
import pytest
from backend.core.risk import classify_checkpoint
from backend.core.types import LatLng, RiskLevel, Weather
from backend.providers.fixture_weather import FixtureWeatherProvider


def test_fixture_weather_storm_corridor_spectrum():
    provider = FixtureWeatherProvider()
    start = datetime(2026, 10, 12, 14, 0, tzinfo=timezone.utc)

    # Chicago (East, mild), Iowa (Moderate/High), Central Nebraska (Severe/Storm peak), Denver (West, Moderate)
    pts = [
        LatLng(lat=41.9, lng=-87.6),   # Chicago
        LatLng(lat=41.6, lng=-93.6),   # Des Moines, IA
        LatLng(lat=41.1, lng=-99.0),   # Storm center (NE)
        LatLng(lat=39.7, lng=-105.0),  # Denver
    ]

    forecasts = provider.get_hourly_forecast(pts, start, start)

    # All coordinates present
    assert (41.9, -87.6) in forecasts
    assert (41.1, -99.0) in forecasts

    # Check series length
    series_center = forecasts[(41.1, -99.0)]
    assert len(series_center.times) >= 49

    # Check storm center produces Severe/No Travel with heavy load (42,000 lb)
    center_w = Weather(
        wind_mph=series_center.wind_mph[0],
        rain_in_hr=series_center.rain_in_hr[0],
        snow_in_hr=series_center.snow_in_hr[0],
    )
    center_risk = classify_checkpoint(center_w, load_lb=42000)
    assert center_risk.level in (RiskLevel.SEVERE, RiskLevel.NO_TRAVEL)

    # Check Chicago is calmer
    chicago_series = forecasts[(41.9, -87.6)]
    chicago_w = Weather(
        wind_mph=chicago_series.wind_mph[0],
        rain_in_hr=chicago_series.rain_in_hr[0],
        snow_in_hr=chicago_series.snow_in_hr[0],
    )
    chicago_risk = classify_checkpoint(chicago_w, load_lb=42000)
    assert chicago_risk.level < center_risk.level
