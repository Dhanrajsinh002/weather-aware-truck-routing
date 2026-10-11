import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest
from backend.core.types import LatLng
from backend.providers.open_meteo import OpenMeteoProvider, round_coord


def test_round_coord():
    assert round_coord(41.8781) == 41.9
    assert round_coord(-87.6298) == -87.6


def test_parse_open_meteo_fixture():
    fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "open_meteo_fixture.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    provider = OpenMeteoProvider()
    series_chicago = provider._parse_hourly_data(data[0])
    series_denver = provider._parse_hourly_data(data[1])

    # Chicago: rain 0.05 + showers 0.00 = 0.05
    assert series_chicago.rain_in_hr[0] == 0.05
    # Hour 1: rain 0.10 + showers 0.05 = 0.15
    assert series_chicago.rain_in_hr[1] == 0.15
    assert series_chicago.wind_mph[0] == 12.0
    assert series_chicago.gust_mph[0] == 18.0

    # Denver: snow = snowfall
    assert series_denver.snow_in_hr[0] == 0.50
    assert series_denver.snow_in_hr[2] == 2.50
    assert series_denver.wind_mph[0] == 8.0


def test_cache_hit():
    provider = OpenMeteoProvider()
    pts = [LatLng(lat=41.8781, lng=-87.6298)]
    now = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)

    # Mock _fetch_batch
    called = []

    def mock_fetch(batch_coords, s, e):
        called.append(batch_coords)
        return {
            (41.9, -87.6): provider._parse_hourly_data({
                "hourly": {
                    "time": ["2026-10-12T12:00"],
                    "wind_speed_10m": [15.0],
                }
            })
        }

    provider._fetch_batch = mock_fetch

    # Call 1: uncached
    res1 = provider.get_hourly_forecast(pts, now, now)
    assert len(called) == 1
    assert (41.9, -87.6) in res1

    # Call 2: cached
    res2 = provider.get_hourly_forecast(pts, now, now)
    assert len(called) == 1  # Not called again
    assert (41.9, -87.6) in res2


@pytest.mark.live_smoke
def test_open_meteo_live_smoke():
    """Live smoke test marked skippable."""
    pytest.skip("Skipping live smoke test to avoid external network dependency in standard runs")
