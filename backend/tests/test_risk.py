import pytest
from backend.core.types import RiskLevel, Weather, RiskResult
from backend.core.risk import (
    classify_wind,
    classify_rain,
    classify_snow,
    apply_load_rules,
    classify_checkpoint,
)


@pytest.mark.parametrize(
    "wind, expected",
    [
        (0.0, RiskLevel.LOW),
        (24.9, RiskLevel.LOW),
        (25.0, RiskLevel.MODERATE),
        (34.9, RiskLevel.MODERATE),
        (35.0, RiskLevel.HIGH),
        (44.9, RiskLevel.HIGH),
        (45.0, RiskLevel.SEVERE),
        (54.9, RiskLevel.SEVERE),
        (55.0, RiskLevel.NO_TRAVEL),
        (70.0, RiskLevel.NO_TRAVEL),
    ],
)
def test_classify_wind_boundaries(wind, expected):
    assert classify_wind(wind) == expected


@pytest.mark.parametrize(
    "rain, expected",
    [
        (0.0, RiskLevel.LOW),
        (0.0999, RiskLevel.LOW),
        (0.10, RiskLevel.MODERATE),
        (0.25, RiskLevel.MODERATE),
        (0.2501, RiskLevel.HIGH),
        (0.50, RiskLevel.HIGH),
        (0.5001, RiskLevel.SEVERE),
        (1.00, RiskLevel.SEVERE),
        (1.0001, RiskLevel.NO_TRAVEL),
        (2.0, RiskLevel.NO_TRAVEL),
    ],
)
def test_classify_rain_boundaries(rain, expected):
    assert classify_rain(rain) == expected


@pytest.mark.parametrize(
    "snow, expected",
    [
        (0.0, RiskLevel.LOW),
        (0.49, RiskLevel.LOW),
        (0.50, RiskLevel.MODERATE),
        (1.0, RiskLevel.MODERATE),
        (1.0001, RiskLevel.HIGH),
        (2.0, RiskLevel.HIGH),
        (2.0001, RiskLevel.SEVERE),
        (3.0, RiskLevel.SEVERE),
        (3.01, RiskLevel.NO_TRAVEL),
        (4.5, RiskLevel.NO_TRAVEL),
    ],
)
def test_classify_snow_boundaries(snow, expected):
    assert classify_snow(snow) == expected


@pytest.mark.parametrize(
    "wind, load, base_level, expected_level, has_escalation",
    [
        # wind >= 55 -> NO_TRAVEL any load
        (55.0, 1000, RiskLevel.NO_TRAVEL, RiskLevel.NO_TRAVEL, False),
        (60.0, 50000, RiskLevel.NO_TRAVEL, RiskLevel.NO_TRAVEL, False),
        # wind 45-54 and load > 30000 -> NO_TRAVEL
        (45.0, 30000, RiskLevel.SEVERE, RiskLevel.SEVERE, False),
        (45.0, 30001, RiskLevel.SEVERE, RiskLevel.NO_TRAVEL, True),
        (54.9, 30000, RiskLevel.SEVERE, RiskLevel.SEVERE, False),
        (54.9, 35000, RiskLevel.SEVERE, RiskLevel.NO_TRAVEL, True),
        # wind 35-44 and load > 40000 -> SEVERE
        (35.0, 40000, RiskLevel.HIGH, RiskLevel.HIGH, False),
        (35.0, 40001, RiskLevel.HIGH, RiskLevel.SEVERE, True),
        (44.9, 40000, RiskLevel.HIGH, RiskLevel.HIGH, False),
        (44.9, 45000, RiskLevel.HIGH, RiskLevel.SEVERE, True),
        # Low wind with heavy load does NOT escalate
        (20.0, 80000, RiskLevel.LOW, RiskLevel.LOW, False),
        # Moderate wind (25-34) with heavy load does NOT escalate
        (30.0, 50000, RiskLevel.MODERATE, RiskLevel.MODERATE, False),
    ],
)
def test_apply_load_rules_boundaries(wind, load, base_level, expected_level, has_escalation):
    level, escalated, _ = apply_load_rules(wind, load, base_level)
    assert level == expected_level
    assert escalated == has_escalation


def test_load_never_lowers_level():
    # Base level is NO_TRAVEL, load is light -> remains NO_TRAVEL
    level, escalated, _ = apply_load_rules(55.0, 1000, RiskLevel.NO_TRAVEL)
    assert level == RiskLevel.NO_TRAVEL

    # Base level SEVERE from wind, light load -> remains SEVERE
    level, escalated, _ = apply_load_rules(48.0, 5000, RiskLevel.SEVERE)
    assert level == RiskLevel.SEVERE


def test_golden_tests():
    """Golden scenarios specified in PLAN.md and instructions."""
    # 1. wind 47 + 35,000 lb = NO_TRAVEL (45-54 and >30k)
    w1 = Weather(wind_mph=47.0)
    r1 = classify_checkpoint(w1, load_lb=35000)
    assert r1.level == RiskLevel.NO_TRAVEL
    assert any("35,000" in d and "No Travel" in d for d in r1.drivers)

    # 2. wind 47 + 25,000 lb = SEVERE
    w2 = Weather(wind_mph=47.0)
    r2 = classify_checkpoint(w2, load_lb=25000)
    assert r2.level == RiskLevel.SEVERE
    assert any("Wind 47.0 mph" in d for d in r2.drivers)

    # 3. wind 38 + 45,000 lb = SEVERE (35-44 and >40k)
    w3 = Weather(wind_mph=38.0)
    r3 = classify_checkpoint(w3, load_lb=45000)
    assert r3.level == RiskLevel.SEVERE
    assert any("45,000" in d and "Severe" in d for d in r3.drivers)

    # 4. wind 38 + 20,000 lb = HIGH
    w4 = Weather(wind_mph=38.0)
    r4 = classify_checkpoint(w4, load_lb=20000)
    assert r4.level == RiskLevel.HIGH
    assert any("Wind 38.0 mph" in d for d in r4.drivers)

    # 5. wind 55 + 1,000 lb = NO_TRAVEL
    w5 = Weather(wind_mph=55.0)
    r5 = classify_checkpoint(w5, load_lb=1000)
    assert r5.level == RiskLevel.NO_TRAVEL
    assert any("Wind 55.0 mph" in d for d in r5.drivers)


def test_classify_checkpoint_calm():
    w = Weather(wind_mph=10.0, rain_in_hr=0.0, snow_in_hr=0.0)
    r = classify_checkpoint(w, load_lb=40000)
    assert r.level == RiskLevel.LOW
    assert r.score == 0
    assert r.drivers == []


def test_classify_checkpoint_rain_dominant():
    w = Weather(wind_mph=15.0, rain_in_hr=0.60, snow_in_hr=0.0)
    r = classify_checkpoint(w, load_lb=40000)
    assert r.level == RiskLevel.SEVERE
    assert r.score == 3
    assert any("Rain 0.60 in/hr" in d for d in r.drivers)


def test_classify_checkpoint_snow_dominant():
    w = Weather(wind_mph=15.0, rain_in_hr=0.0, snow_in_hr=3.5)
    r = classify_checkpoint(w, load_lb=20000)
    assert r.level == RiskLevel.NO_TRAVEL
    assert r.score == 4
    assert any("Snow 3.50 in/hr" in d for d in r.drivers)
