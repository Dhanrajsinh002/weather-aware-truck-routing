import json
from pathlib import Path
import pytest
from backend.providers.photon import PhotonProvider, format_photon_label


def test_format_photon_label():
    props1 = {"name": "Chicago", "state": "Illinois", "country": "United States"}
    assert format_photon_label(props1) == "Chicago, Illinois, United States"

    props2 = {"name": "Denver", "country": "United States"}
    assert format_photon_label(props2) == "Denver, United States"


def test_parse_photon_fixture():
    fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "photon_fixture.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    provider = PhotonProvider()
    results = provider._parse_response(data)

    assert len(results) == 2
    assert results[0].label == "Chicago, Illinois, United States"
    assert results[0].lat == 41.8781
    assert results[0].lng == -87.6298

    assert results[1].label == "Denver, Colorado, United States"
    assert results[1].lat == 39.7392
    assert results[1].lng == -104.9903
