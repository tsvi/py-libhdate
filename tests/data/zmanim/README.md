# Zmanim Reference Testing System

This directory contains the infrastructure for validating py-libhdate's zmanim calculations against external reference sources.

## Overview

The system allows you to:
1. Define "interesting locations" and "interesting times" in a manifest
2. Fetch reference data from external APIs (currently Hebcal)
3. Automatically compare py-libhdate calculations against the reference
4. Detect and handle known calculation differences

## Workflow

### When a bug is reported

1. **Add location/date to manifest** ([manifest.json](manifest.json)):
   ```json
   {
     "dates": ["2024-03-20", "2024-06-18", "2024-12-18", "2025-01-15"],
     "locations": [
       {
         "name": "Bug Report City",
         "latitude": 12.34,
         "longitude": -56.78,
         "tzid": "America/New_York",
         "tolerance_minutes": 3
       }
     ]
   }
   ```

2. **Fetch reference data**:
   ```bash
   python utils/fetch_zmanim_reference.py \
     --manifest tests/data/zmanim/manifest.json \
     --output tests/data/zmanim/hebcal_reference.json
   ```

3. **Run the tests**:
   ```bash
   pytest tests/test_zmanim_reference.py -v
   ```

4. **Analyze results**:
   - Passing tests: py-libhdate matches the reference
   - Failing tests: Identify calculation differences
   - Skipped tests: Known issues (day boundaries, etc.)

## Files

- **[manifest.json](manifest.json)**: Configuration of locations and dates to test
- **[hebcal_reference.json](hebcal_reference.json)**: Reference data from Hebcal API (generated)
- **[SOURCES.md](SOURCES.md)**: Documentation of available data sources and their differences
- **[utils/fetch_zmanim_reference.py](../../utils/fetch_zmanim_reference.py)**: Scraper script
- **[tests/test_zmanim_reference.py](../../test_zmanim_reference.py)**: Parametrized pytest tests

## Current Test Coverage

### Locations
- New York, US (40.71°N, 74.01°W) - Standard US location
- Jerusalem, IL (31.78°N, 35.24°E) - Israel, different customs
- London, UK (51.51°N, 0.13°W) - High latitude Europe
- Sydney, AU (-33.87°S, 151.21°E) - Southern hemisphere
- Reykjavik, IS (64.15°N, 21.94°W) - Very high latitude

### Dates
- 2024-03-20 (Spring Equinox) - Equal day/night
- 2024-06-18 (Summer, near solstice) - Long days
- 2024-12-18 (Winter, near solstice) - Short days

## Known Issues and Handling

### Day Boundary Differences

**Issue**: For locations where local date ≠ UTC date (southern hemisphere, far time zones), calculated times may be on different calendar days.

**Detection**: Automatically detected when times differ by ~24 hours (1440 minutes).

**Handling**: Tests are skipped with informative message.

**Example**: Sydney's `alot_hashachar` on 2024-03-20 appears on 2024-03-21 in local time.

### Midnight (chatzot_halayla)

**Issue**: Hebcal reports midnight for the night that *starts* the day; py-libhdate reports it for the night that *ends* the day.

**Handling**: Excluded from comparison in `EXCLUDED_ZMANIM` set.

### Misheyakir Variation

**Issue**: Different sources use different degree calculations for misheyakir, especially at high latitudes.

**Handling**: Higher tolerance values:
- Normal: 8 minutes
- High latitude (≥55°): 12 minutes

## Tolerance Values

Tests allow for small calculation differences:

| Location Type | Base Tolerance | Misheyakir | Notes |
|--------------|----------------|------------|-------|
| Standard | 3 min | 8 min | Most locations |
| High latitude (≥55°) | 10 min | 12 min | Reykjavik, etc. |
| Without astral | 5 min | 8 min | Fallback calculations |

Tolerances are configurable per-location in the manifest.

## Adding New Reference Sources

See [SOURCES.md](SOURCES.md) for:
- Available APIs (Hebcal, MyZmanim, Chabad, etc.)
- Implementation guidelines
- Field mappings
- License requirements

## Usage Examples

### Test a specific location
```bash
pytest tests/test_zmanim_reference.py -v -k "New York"
```

### Test a specific date
```bash
pytest tests/test_zmanim_reference.py -v -k "2024-06-18"
```

### Show skipped tests
```bash
pytest tests/test_zmanim_reference.py -v -rs
```

### Re-fetch reference data
```bash
# Fetch all data from manifest
python utils/fetch_zmanim_reference.py

# Or specify paths explicitly
python utils/fetch_zmanim_reference.py \
  --manifest tests/data/zmanim/manifest.json \
  --output tests/data/zmanim/hebcal_reference.json
```

## Continuous Integration

These tests are part of the standard test suite and run on every commit. They help ensure:
- Calculation accuracy across diverse locations
- Consistency with established authorities
- Early detection of regressions

## Credits

Reference data sourced from:
- **Hebcal.com** - Licensed under CC-BY-4.0
  - Must provide attribution when using
  - Documentation: https://www.hebcal.com/home/developer-apis

## Future Enhancements

- Add more reference sources for cross-validation
- Implement multi-source consensus checking
- Add seasonal variation tests (summer/winter extremes)
- Test edge cases (polar regions, equator)
- Generate visual comparison reports
