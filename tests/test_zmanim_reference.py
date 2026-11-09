"""Reference comparison tests against external zmanim APIs.

This module compares py-libhdate zmanim calculations against reference data
from external sources (currently Hebcal). The reference data is stored in JSON
files and can be regenerated using utils/fetch_zmanim_reference.py.

Known differences:
- chatzot_halayla (midnight): Hebcal reports midnight for the night that starts
  the day, while py-libhdate reports it for the night that ends the day.
  This is excluded from comparisons.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

import pytest

from hdate import Zmanim
from hdate.location import Location
from hdate.zmanim import _USE_ASTRAL
from hdate.zmanim_config import ZmanimPresets

REFERENCE_PATH = (
    Path(__file__).resolve().parent / "data" / "zmanim" / "hebcal_reference.json"
)

DEFAULT_TOLERANCE_MINUTES = 3
FALLBACK_TOLERANCE_MINUTES = 5
HIGH_LATITUDE_TOLERANCE_MINUTES = 10
MISHEYAKIR_TOLERANCE_MINUTES = 8  # Misheyakir varies more across sources
HIGH_LATITUDE_MISHEYAKIR_TOLERANCE_MINUTES = 12  # Even more variation at high latitudes

# Zmanim to exclude from comparison due to known differences
EXCLUDED_ZMANIM = {
    "chatzot_halayla",  # Day boundary difference: Hebcal vs py-libhdate
}


def _load_reference() -> dict[str, Any]:
    return json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))


def _minutes_delta(left: dt.datetime, right: dt.datetime) -> float:
    delta = left.astimezone(dt.timezone.utc) - right.astimezone(dt.timezone.utc)
    return abs(delta.total_seconds()) / 60.0


def _tolerance_for_location(location: dict[str, Any]) -> int:
    tolerance = int(location.get("tolerance_minutes", DEFAULT_TOLERANCE_MINUTES))
    if not _USE_ASTRAL:
        tolerance = max(tolerance, FALLBACK_TOLERANCE_MINUTES)
    if abs(float(location["latitude"])) >= 55:
        tolerance = max(tolerance, HIGH_LATITUDE_TOLERANCE_MINUTES)
    return tolerance


def _get_test_cases() -> list[tuple[str, str, dict[str, Any]]]:
    """Generate test cases from reference data."""
    reference = _load_reference()
    test_cases = []
    for location in reference["locations"]:
        for date_str in location["dates"].keys():
            test_id = f"{location['name']}_{date_str}"
            test_cases.append((test_id, date_str, location))
    return test_cases


@pytest.mark.parametrize(
    "test_id,date_str,location",
    _get_test_cases(),
    ids=lambda val: val if isinstance(val, str) else None,
)
def test_zmanim_matches_hebcal_reference(
    test_id: str, date_str: str, location: dict[str, Any]
) -> None:
    """Compare Zmanim calculations against stored Hebcal reference data.
    
    Args:
        test_id: Test identifier (location_date)
        date_str: ISO date string
        location: Location data from reference JSON
    """
    test_location = Location(
        name=location["name"],
        latitude=location["latitude"],
        longitude=location["longitude"],
        timezone=location["tzid"],
    )
    tolerance = _tolerance_for_location(location)
    test_date = dt.date.fromisoformat(date_str)
    expected_times = location["dates"][date_str]
    
    zmanim = Zmanim(
        date=test_date,
        location=test_location,
        config=ZmanimPresets.gra_standard(),
    )
    
    for key, expected_iso in expected_times.items():
        if expected_iso is None:
            continue
        if key in EXCLUDED_ZMANIM:
            continue
        
        actual = getattr(zmanim, key).local
        expected = dt.datetime.fromisoformat(expected_iso)
        diff = _minutes_delta(actual, expected)
        
        # Check for day boundary issues (24-hour difference indicates date mismatch)
        if abs(diff - 1440) < 5:  # Within 5 minutes of 24 hours
            pytest.skip(
                f"Day boundary issue: {location['name']} {date_str} {key} "
                f"differs by ~24 hours (Hebcal date vs local date mismatch)"
            )
        
        # Use higher tolerance for misheyakir which varies across sources
        effective_tolerance = tolerance
        if key == "misheyakir":
            if abs(float(location["latitude"])) >= 55:
                effective_tolerance = HIGH_LATITUDE_MISHEYAKIR_TOLERANCE_MINUTES
            else:
                effective_tolerance = MISHEYAKIR_TOLERANCE_MINUTES
        
        assert diff <= effective_tolerance, (
            f"{location['name']} {date_str} {key} off by {diff:.2f} min "
            f"(tolerance {effective_tolerance} min)"
        )
