import pytest
from backend.core.types import LatLng
from backend.providers.base import (
    RoutingProvider,
    WeatherProvider,
    GeocodeProvider,
    ProviderError,
    RoutingError,
    NoRouteFoundError,
    WeatherServiceError,
    GeocodeError,
    GeocodeResult,
)


def test_exception_hierarchy():
    err = NoRouteFoundError("No truck route found")
    assert isinstance(err, RoutingError)
    assert isinstance(err, ProviderError)
    assert err.code == "NO_ROUTE"

    w_err = WeatherServiceError("Weather service down")
    assert isinstance(w_err, ProviderError)
    assert w_err.code == "UPSTREAM"
    assert w_err.provider == "weather"


def test_geocode_result_dataclass():
    res = GeocodeResult(label="Chicago, IL", lat=41.8781, lng=-87.6298)
    assert res.label == "Chicago, IL"
    assert res.lat == 41.8781
    assert res.lng == -87.6298
