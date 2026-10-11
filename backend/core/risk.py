"""Pure Python risk classification for weather-aware truck routing.

No I/O, no Django imports.
"""

from __future__ import annotations

from typing import List, Tuple
from backend.core.types import RiskLevel, RiskResult, Weather


def classify_wind(wind_mph: float) -> RiskLevel:
    """Classify sustained wind speed (mph) into a RiskLevel.

    Thresholds:
    < 25: LOW
    [25, 35): MODERATE
    [35, 45): HIGH
    [45, 55): SEVERE
    >= 55: NO_TRAVEL
    """
    if wind_mph >= 55.0:
        return RiskLevel.NO_TRAVEL
    if wind_mph >= 45.0:
        return RiskLevel.SEVERE
    if wind_mph >= 35.0:
        return RiskLevel.HIGH
    if wind_mph >= 25.0:
        return RiskLevel.MODERATE
    return RiskLevel.LOW


def classify_rain(rain_in_hr: float) -> RiskLevel:
    """Classify hourly rainfall (in/hr) into a RiskLevel.

    Thresholds (upper-inclusive):
    < 0.10: LOW
    [0.10, 0.25]: MODERATE
    (0.25, 0.50]: HIGH
    (0.50, 1.00]: SEVERE
    > 1.00: NO_TRAVEL
    """
    if rain_in_hr > 1.00:
        return RiskLevel.NO_TRAVEL
    if rain_in_hr > 0.50:
        return RiskLevel.SEVERE
    if rain_in_hr > 0.25:
        return RiskLevel.HIGH
    if rain_in_hr >= 0.10:
        return RiskLevel.MODERATE
    return RiskLevel.LOW


def classify_snow(snow_in_hr: float) -> RiskLevel:
    """Classify hourly snowfall (in/hr) into a RiskLevel.

    Thresholds (upper-inclusive):
    < 0.5: LOW
    [0.5, 1.0]: MODERATE
    (1.0, 2.0]: HIGH
    (2.0, 3.0]: SEVERE
    > 3.0: NO_TRAVEL
    """
    if snow_in_hr > 3.0:
        return RiskLevel.NO_TRAVEL
    if snow_in_hr > 2.0:
        return RiskLevel.SEVERE
    if snow_in_hr > 1.0:
        return RiskLevel.HIGH
    if snow_in_hr >= 0.5:
        return RiskLevel.MODERATE
    return RiskLevel.LOW


def apply_load_rules(
    wind_mph: float,
    load_lb: float,
    base_level: RiskLevel,
) -> Tuple[RiskLevel, bool, str]:
    """Apply load weight rules to adjust wind-induced risk level.

    Rules:
    - wind >= 55 mph -> NO_TRAVEL for any load
    - wind in [45, 55) mph and load > 30,000 lb -> NO_TRAVEL
    - wind in [35, 45) mph and load > 40,000 lb -> SEVERE
    - Load rules can only RAISE a level, never lower it.

    Returns:
    (effective_level, was_escalated, escalation_driver)
    """
    level = base_level
    escalated = False
    driver = ""

    if wind_mph >= 55.0:
        level = RiskLevel.NO_TRAVEL
    elif 45.0 <= wind_mph < 55.0 and load_lb > 30000:
        if RiskLevel.NO_TRAVEL > level:
            level = RiskLevel.NO_TRAVEL
            escalated = True
            driver = f"Wind {wind_mph:.1f} mph + load {load_lb:,.0f} lb → No Travel"
    elif 35.0 <= wind_mph < 45.0 and load_lb > 40000:
        if RiskLevel.SEVERE > level:
            level = RiskLevel.SEVERE
            escalated = True
            driver = f"Wind {wind_mph:.1f} mph + load {load_lb:,.0f} lb → Severe"

    # Ensure load rule never lowers risk level
    if level < base_level:
        level = base_level

    return level, escalated, driver


def format_level_name(level: RiskLevel) -> str:
    """Format RiskLevel enum as human-friendly string."""
    names = {
        RiskLevel.LOW: "Low",
        RiskLevel.MODERATE: "Moderate",
        RiskLevel.HIGH: "High",
        RiskLevel.SEVERE: "Severe",
        RiskLevel.NO_TRAVEL: "No Travel",
    }
    return names.get(level, level.name)


def classify_checkpoint(weather: Weather, load_lb: float) -> RiskResult:
    """Classify overall risk for a checkpoint given weather and load.

    Checkpoint level = max(wind, rain, snow levels after load rules).
    Returns RiskResult with level, numeric score, and human-readable drivers.
    """
    base_wind_level = classify_wind(weather.wind_mph)
    wind_level, wind_escalated, wind_driver = apply_load_rules(
        weather.wind_mph, load_lb, base_wind_level
    )

    rain_level = classify_rain(weather.rain_in_hr)
    snow_level = classify_snow(weather.snow_in_hr)

    final_level = max(wind_level, rain_level, snow_level)

    drivers: List[str] = []

    if final_level > RiskLevel.LOW:
        # Check if wind contributed
        if wind_level == final_level:
            if wind_escalated:
                drivers.append(wind_driver)
            else:
                drivers.append(
                    f"Wind {weather.wind_mph:.1f} mph → {format_level_name(wind_level)}"
                )

        # Check if rain contributed
        if rain_level == final_level and weather.rain_in_hr > 0.0:
            drivers.append(
                f"Rain {weather.rain_in_hr:.2f} in/hr → {format_level_name(rain_level)}"
            )

        # Check if snow contributed
        if snow_level == final_level and weather.snow_in_hr > 0.0:
            drivers.append(
                f"Snow {weather.snow_in_hr:.2f} in/hr → {format_level_name(snow_level)}"
            )

    return RiskResult(
        level=final_level,
        score=int(final_level),
        drivers=drivers,
    )
