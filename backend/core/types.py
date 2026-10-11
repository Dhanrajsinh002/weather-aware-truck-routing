"""Core domain types for weather-aware truck routing.

Pure Python dataclasses and enums. No external dependencies, no I/O, no Django imports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import List, Optional


class RiskLevel(IntEnum):
    """Weather travel risk levels."""

    LOW = 0
    MODERATE = 1
    HIGH = 2
    SEVERE = 3
    NO_TRAVEL = 4


@dataclass(frozen=True)
class LatLng:
    """Geographic coordinate."""

    lat: float
    lng: float


@dataclass(frozen=True)
class Weather:
    """Weather metrics at a given point and time."""

    wind_mph: float = 0.0
    gust_mph: float = 0.0
    rain_in_hr: float = 0.0
    snow_in_hr: float = 0.0


@dataclass
class RiskResult:
    """Evaluated risk level and human-readable explanation drivers."""

    level: RiskLevel
    score: int
    drivers: List[str] = field(default_factory=list)


@dataclass
class Checkpoint:
    """A sampled checkpoint along a route."""

    index: int
    mile: float
    lat: float
    lng: float
    eta: datetime
    weather: Optional[Weather] = None
    risk: Optional[RiskResult] = None
    owned_miles: float = 0.0


@dataclass
class RouteMetrics:
    """Aggregated risk metrics for a route."""

    no_travel_miles: float
    severe_miles: float
    high_miles: float
    avg_risk: float
    max_level: RiskLevel


@dataclass
class Route:
    """A generated travel route option."""

    id: str
    label: str
    distance_miles: float
    duration_seconds: float
    geometry: List[List[float]] = field(default_factory=list)  # [[lng, lat], ...]
    checkpoints: List[Checkpoint] = field(default_factory=list)
    metrics: Optional[RouteMetrics] = None
    rank: int = 0
    recommended: bool = False


@dataclass
class Recommendation:
    """Final routing recommendation and comparison rationale."""

    route_id: str
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class HeatmapPoint:
    """Corridor heatmap point with 49-hour forecast risk levels."""

    lat: float
    lng: float
    levels: List[int] = field(default_factory=list)  # 49 integer risk levels (0-4)
