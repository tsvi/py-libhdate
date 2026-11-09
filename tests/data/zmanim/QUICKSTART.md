# Quick Start: Adding a Bug Report Location

## Scenario
Someone reports: "Zmanim times are wrong for Miami on December 25, 2025"

## Steps

### 1. Add to Manifest (30 seconds)

Edit `tests/data/zmanim/manifest.json`:

```json
{
  "sources": ["hebcal"],
  "dates": [
    "2024-03-20", 
    "2024-06-18", 
    "2024-12-18",
    "2025-12-25"    // ← ADD THIS
  ],
  "locations": [
    // ... existing locations ...
    {
      "name": "Miami, US",         // ← ADD THIS BLOCK
      "latitude": 25.7617,
      "longitude": -80.1918,
      "tzid": "America/New_York",
      "tolerance_minutes": 3
    }
  ]
}
```

### 2. Fetch Reference Data (10 seconds)

```bash
python utils/fetch_zmanim_reference.py
```

Output:
```
Wrote tests/data/zmanim/hebcal_reference.json
```

### 3. Run Tests (5 seconds)

```bash
pytest tests/test_zmanim_reference.py -v -k Miami
```

### 4. Interpret Results

#### ✅ All Pass
```
test_zmanim_matches_hebcal_reference[Miami, US_2025-12-25] PASSED
```
**Meaning**: Our calculations match Hebcal within tolerance. The bug might be:
- User error (wrong date/location)
- Different calculation method expected
- UI/display issue rather than calculation

#### ❌ Some Fail
```
test_zmanim_matches_hebcal_reference[Miami, US_2025-12-25] FAILED
AssertionError: Miami, US 2025-12-25 shkia off by 15.23 min (tolerance 3 min)
```
**Meaning**: Real calculation error found! Investigate `shkia` calculation.

#### ⏭️ Skipped
```
test_zmanim_matches_hebcal_reference[Miami, US_2025-12-25] SKIPPED
Day boundary issue: differs by ~24 hours
```
**Meaning**: Date/timezone mismatch, probably not a real bug.

## Complete Example Session

```bash
# 1. Edit manifest
vim tests/data/zmanim/manifest.json

# 2. Fetch data
python utils/fetch_zmanim_reference.py
# Output: Wrote tests/data/zmanim/hebcal_reference.json

# 3. Run new tests only
pytest tests/test_zmanim_reference.py -v -k "Miami or 2025-12-25"

# 4. If failures, run with verbose output
pytest tests/test_zmanim_reference.py -v -k Miami --tb=short

# 5. Compare specific zman
python -c "
from datetime import date
from hdate import Zmanim, Location

loc = Location('Miami', 25.7617, -80.1918, 'America/New_York')
z = Zmanim(date(2025, 12, 25), loc)
print(f'Shkia: {z.shkia.local}')
print(f'Expected from Hebcal: (check reference.json)')
"
```

## Tips for Different Scenarios

### High Latitude Location (>55°)
```json
{
  "name": "Anchorage, US",
  "latitude": 61.2181,
  "longitude": -149.9003,
  "tzid": "America/Anchorage",
  "tolerance_minutes": 10  // ← Higher tolerance
}
```

### Southern Hemisphere
Expect some tests to skip due to day boundary differences. This is normal.

### Different Seasons
Add 3-4 dates covering solstices and equinoxes:
```json
"dates": [
  "2025-03-20",  // Spring equinox
  "2025-06-21",  // Summer solstice
  "2025-09-23",  // Fall equinox
  "2025-12-21"   // Winter solstice
]
```

## Troubleshooting

### "No module named 'hdate'"
```bash
# Activate virtual environment first
source .venv/bin/activate  # or: pdm shell
```

### Network timeout fetching reference
```bash
# Increase timeout in fetch_zmanim_reference.py
with urlopen(url, timeout=60) as response:  # was 30
```

### All tests fail for new location
Check your manifest JSON syntax:
```bash
python -m json.tool tests/data/zmanim/manifest.json
```

## What to Do With Results

### Tests Pass ✅
Document in the GitHub issue that calculations are correct per Hebcal reference.

### Tests Fail ❌
1. Check if it's a known difference (see `SOURCES.md`)
2. Investigate the calculation code
3. File a detailed bug report with:
   - Location details
   - Date
   - Expected vs actual times
   - Reference source (Hebcal)

### Tests Skip ⏭️
Investigate if it's a real date/timezone issue or just day boundary mismatch.

## Next Steps

After validating:
1. Keep the location in manifest for regression testing
2. Document any fixes made
3. Re-run full test suite: `pytest tests/test_zmanim_reference.py`
