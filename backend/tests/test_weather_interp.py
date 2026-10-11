import pytest
from datetime import datetime, timezone, timedelta
from backend.core.weather_interp import (
    HourlySeries,
    interpolate_weather_at_time,
)
from backend.core.types import Weather


@pytest.fixture
def sample_hourly_series():
    base_time = datetime(2026, 10, 12, 12, 0, 0, tzinfo=timezone.utc)
    times = [base_time + timedelta(hours=i) for i in range(5)]
    # Hour 0: 10 mph wind, 0 rain, 0 snow
    # Hour 1: 20 mph wind, 0.20 rain, 0.5 snow
    # Hour 2: 30 mph wind, 0.40 rain, 1.0 snow
    # Hour 3: 40 mph wind, 0.60 rain, 1.5 snow
    # Hour 4: 50 mph wind, 0.80 rain, 2.0 snow
    return HourlySeries(
        times=times,
        wind_mph=[10.0, 20.0, 30.0, 40.0, 50.0],
        gust_mph=[15.0, 25.0, 35.0, 45.0, 55.0],
        rain_in_hr=[0.0, 0.20, 0.40, 0.60, 0.80],
        snow_in_hr=[0.0, 0.50, 1.00, 1.50, 2.00],
    )


def test_interpolate_exact_hour(sample_hourly_series):
    t = sample_hourly_series.times[1]  # hour 1
    w, unavailable = interpolate_weather_at_time(sample_hourly_series, t)
    assert not unavailable
    assert w.wind_mph == 20.0
    assert w.gust_mph == 25.0
    assert w.rain_in_hr == 0.20
    assert w.snow_in_hr == 0.50


def test_interpolate_half_hour(sample_hourly_series):
    # Hour 1.5 (between hour 1 and 2)
    t = sample_hourly_series.times[1] + timedelta(minutes=30)
    w, unavailable = interpolate_weather_at_time(sample_hourly_series, t)
    assert not unavailable
    assert pytest.approx(w.wind_mph) == 25.0
    assert pytest.approx(w.gust_mph) == 30.0
    assert pytest.approx(w.rain_in_hr) == 0.30
    assert pytest.approx(w.snow_in_hr) == 0.75


def test_interpolate_fractional_time(sample_hourly_series):
    # 15 minutes past hour 2 (25% between hour 2 and 3)
    t = sample_hourly_series.times[2] + timedelta(minutes=15)
    w, unavailable = interpolate_weather_at_time(sample_hourly_series, t)
    assert not unavailable
    assert pytest.approx(w.wind_mph) == 32.5
    assert pytest.approx(w.rain_in_hr) == 0.45


def test_before_horizon_clamping(sample_hourly_series):
    t_before = sample_hourly_series.times[0] - timedelta(hours=2)
    w, unavailable = interpolate_weather_at_time(sample_hourly_series, t_before)
    assert unavailable is True
    # Clamped to first available hour
    assert w.wind_mph == 10.0


def test_after_horizon_clamping(sample_hourly_series):
    t_after = sample_hourly_series.times[-1] + timedelta(hours=5)
    w, unavailable = interpolate_weather_at_time(sample_hourly_series, t_after)
    assert unavailable is True
    # Clamped to last available hour
    assert w.wind_mph == 50.0
    assert w.snow_in_hr == 2.00


def test_empty_series():
    empty = HourlySeries(times=[], wind_mph=[], gust_mph=[], rain_in_hr=[], snow_in_hr=[])
    t = datetime(2026, 10, 12, 12, 0, 0, tzinfo=timezone.utc)
    w, unavailable = interpolate_weather_at_time(empty, t)
    assert unavailable is True
    assert w == Weather()
