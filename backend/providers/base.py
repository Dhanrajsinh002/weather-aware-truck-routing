"""Abstract provider interfaces and domain error types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Sequence, Tuple
from backend.core.types import LatLng, Route
from backend.core.weather_interp import HourlySeries


class ProviderError(Exception):
    """Base exception for external provider issues."""

    def __init__(self, message: str, code: str = "PROVIDER_ERROR", status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class RoutingError(ProviderError):
    """Routing service failed or returned unexpected response."""

    def __init__(self, message: str, code: str = "ROUTING_ERROR", status_code: int = 502):
        super().__init__(message, code=code, status_code=status_code)


class NoRouteFoundError(RoutingError):
    """No viable route could be found for given locations."""

    def __init__(self, message: str = "No viable route found"):
        super().__init__(message, code="NO_ROUTE", status_code=422)


class WeatherServiceError(ProviderError):
    """Weather service failed or timed out."""

    def __init__(self, message: str = "Weather upstream provider failed", provider: str = "weather"):
        super().__init__(message, code="UPSTREAM", status_code=502)
        self.provider = provider


class GeocodeError(ProviderError):
    """Geocoding service failure."""

    def __init__(self, message: str = "Geocoding failed"):
        super().__init__(message, code="GEOCODE_ERROR", status_code=502)


class RateLimitError(ProviderError):
    """Upstream service rate limited."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, code="RATE_LIMITED", status_code=429)


@dataclass(frozen=True)
class GeocodeResult:
    """Geocoding search result."""

    label: str
    lat: float
    lng: float


class RoutingProvider(ABC):
    """Abstract interface for route calculation providers."""

    @abstractmethod
    def get_routes(self, origin: LatLng, destination: LatLng, weight_lb: float) -> List[Route]:
        """Calculate routes between origin and destination for given truck load weight."""
        pass


class WeatherProvider(ABC):
    """Abstract interface for weather forecast providers."""

    @abstractmethod
    def get_hourly_forecast(
        self,
        points: Sequence[LatLng],
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[Tuple[float, float], HourlySeries]:
        """Fetch hourly weather forecasts for given coordinates."""
        pass


class GeocodeProvider(ABC):
    """Abstract interface for location search providers."""

    @abstractmethod
    def search(self, query: str) -> List[GeocodeResult]:
        """Search locations matching query string."""
        pass
