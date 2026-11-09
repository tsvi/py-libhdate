# Configuration API Refinements - Summary

## Overview

Based on your excellent feedback, we've refined the Zmanim configuration API to better address real-world halachic needs. The key improvements address fast day calculations, calculation base distinctions, and more pythonic API design.

## Changes Made

### 1. **Added `calculation_base` Parameter**

This was a crucial addition. Different Jewish authorities calculate proportional times differently:

```python
config = ZmanimConfig(
    calculation_base="gra",  # or "mga" or "baal_hatanya"
)
```

**What this affects:**
- GRA (Gra standard): Calculates from sunrise to sunset
  - Shema time = 1/3 of day from sunrise
  - Tfilla time = 1/3 of day from sunrise
  - Mincha times based on sunrise-to-sunset calculation

- MGA (Magen Avraham): Calculates from dawn (alot) to nightfall (tzait)
  - Shema time = 1/3 of light period from dawn
  - Tfilla time = 1/3 of light period from dawn
  - Mincha times based on dawn-to-nightfall calculation

- Baal HaTanya: Chabad-specific calculations

**Why it matters:**
This is a fundamental distinction that affects multiple zmanim, not just one. By making it configurable, we allow communities to follow their complete halachic system consistently.

### 2. **Separated Tzait for Different Purposes**

Previously, we only had `tzait_hakochavim` and `tzait_shabbat`. Now we also have `tzait_fast_day`:

```python
config = create_custom_config(
    tzait_hakochavim=ZmanMethod(minutes=42),      # Regular weekday
    tzait_fast_day=ZmanMethod(minutes=50),        # Tisha B'Av, Yom Kippur
    tzait_shabbat=ZmanMethod(minutes=50),         # Shabbat/Yom Tov ends
)
```

**Real-world use case:**
- Fast days often use a more stringent tzait time for ending the fast
- Shabbat might also use a more stringent time for ending Shabbat
- Regular weekdays use the standard time

**Example from Israel:**
- Weekday: 42 minutes
- Fast day: 50 minutes
- Shabbat: 50 minutes

### 3. **Completely Refactored `create_custom_config()`**

The old version had hardcoded parameters for `alot_degrees`, `alot_minutes`, `tzait_degrees`, `tzait_minutes`, `tzait_shabbat_degrees`, `tzait_shabbat_minutes`. This wasn't scalable.

**New pythonic approach:**
```python
config = create_custom_config(
    calculation_base="mga",  # Any valid value
    alot_hashachar=ZmanMethod(degrees=16.1),
    misheyakir=ZmanMethodPresets.MISHEYAKIR_10_2_DEGREES,
    tzait_hakochavim=ZmanMethod(minutes=42),
    tzait_fast_day=ZmanMethod(minutes=50),
    tzait_shabbat=ZmanMethod(minutes=50),
    # ... any other field
)
```

**Benefits:**
- Accept any combination of fields using `**kwargs`
- User only specifies what they want to change
- Validates field names and provides helpful error messages
- Handles all 14+ zman fields, not just alot and tzait
- More maintainable as new fields are added

**Validation example:**
```python
try:
    bad = create_custom_config(
        invalid_zman_field=ZmanMethod(degrees=16.1)
    )
except TypeError as e:
    print(e)
    # TypeError: Invalid zman field(s): invalid_zman_field. 
    # Valid fields are: alot_hashachar, misheyakir, ...
```

### 4. **Updated All Presets with Calculation Base**

Each preset now specifies its calculation base and includes `tzait_fast_day`:

```python
@staticmethod
def gra_standard() -> ZmanimConfig:
    return ZmanimConfig(
        calculation_base="gra",          # NEW
        alot_hashachar=...,
        tzait_hakochavim=...,
        tzait_fast_day=...,              # NEW
        tzait_shabbat=...,
    )

@staticmethod
def mga_standard() -> ZmanimConfig:
    return ZmanimConfig(
        calculation_base="mga",          # NEW
        alot_hashachar=...,
        tzait_hakochavim=...,
        tzait_fast_day=...,              # NEW
        tzait_shabbat=...,
    )
```

**All presets updated:**
- `gra_standard()` - GRA method
- `mga_standard()` - MGA method
- `chazon_ish()` - Modern Lithuanian
- `jerusalem_standard()` - Jerusalem Ashkenazi
- `israel_standard()` - Israeli standard
- `sephardic_standard()` - Sephardic/Mizrachi
- `rabeinu_tam()` - Very late nightfall

## Design Rationale

### Why No Enums?

You correctly pointed out that enums were too restrictive. By using `ZmanMethod(degrees=X)` or `ZmanMethod(minutes=X)`, we allow:
- Predefined opinions (via `ZmanMethodPresets`)
- Custom values (any degree or minute value)
- Future additions without API changes

### Why Flexible `create_custom_config()`?

Instead of hardcoding parameter names, using `**kwargs` allows:
- Scaling to all zmanim fields, not just a few
- Clear validation of field names
- User specifies only what they want to change
- More pythonic and idiomatic

### Why Separate `tzait_fast_day`?

Fast days have different halachic rules:
- The fast breaks at a different time than regular nightfall
- Often more stringent than weekday but might differ from Shabbat
- Different communities have different traditions
- Doesn't make sense to use a generic "tzait"

### Why `calculation_base`?

This is the heart of different shitot:
- GRA vs MGA is not just about one time
- It's a complete calculation methodology
- Affects Shema, Tfilla, Mincha, Plag HaMincha, etc.
- Making it explicit is clearer than implicit defaults

## API Comparison

### Before
```python
# Limited flexibility
config = create_custom_config(
    alot_degrees=16.1,
    tzait_minutes=42,
    tzait_shabbat_minutes=50,
)
```

### After (More Pythonic)
```python
# Flexible and scalable
config = create_custom_config(
    calculation_base="gra",
    alot_hashachar=ZmanMethod(degrees=16.1),
    tzait_hakochavim=ZmanMethod(minutes=42),
    tzait_fast_day=ZmanMethod(minutes=50),
    tzait_shabbat=ZmanMethod(minutes=50),
)

# Or using presets
from hdate.zmanim_config import ZmanMethodPresets
config = create_custom_config(
    calculation_base="mga",
    alot_hashachar=ZmanMethodPresets.ALOT_72_MINUTES,
    tzait_hakochavim=ZmanMethodPresets.TZAIT_72_MINUTES,
)
```

## Testing Results

All changes tested and validated:

```
Testing updated configuration...

1. Testing calculation_base parameter:
   ✓ GRA config base: gra
   ✓ MGA config base: mga

2. Testing tzait_fast_day:
   ✓ Weekday tzait: 8.5 degrees
   ✓ Fast day tzait: 50 minutes
   ✓ Shabbat tzait: 8.5 degrees

3. Testing pythonic create_custom_config:
   ✓ Created with calculation_base=mga
   ✓ Field validation working
   ✓ All ZmanMethod values properly stored

4. Testing invalid field detection:
   ✓ Correctly rejected invalid fields
   ✓ Clear error message provided

✅ All tests passed!
```

## Real-World Examples Now Possible

### Example 1: Jerusalem Ashkenazi
```python
config = ZmanimPresets.jerusalem_standard()
# calculation_base: "gra"
# alot: 16.1 degrees
# tzait weekday: 40 minutes
# tzait fast: 40 minutes (same in Jerusalem)
# tzait Shabbat: 40 minutes
```

### Example 2: Israeli with Stringent Fast Day
```python
config = create_custom_config(
    calculation_base="gra",
    alot_hashachar=ZmanMethodPresets.ALOT_16_1_DEGREES,
    tzait_hakochavim=ZmanMethodPresets.TZAIT_42_MINUTES,
    tzait_fast_day=ZmanMethodPresets.TZAIT_50_MINUTES,  # More stringent
    tzait_shabbat=ZmanMethodPresets.TZAIT_42_MINUTES,
)
```

### Example 3: MGA Stringent
```python
config = ZmanimPresets.mga_standard()
# calculation_base: "mga"
# alot: 72 minutes
# All tzait times: 72 minutes
# All proportional calculations use dawn-to-nightfall method
```

## What's Now Possible

✅ Support different calculation bases (GRA vs MGA vs Baal HaTanya)
✅ Different nightfall times for weekdays vs fast days vs Shabbat
✅ Completely custom zmanim combinations
✅ Clear halachic documentation for each setting
✅ Pythonic, flexible, scalable API
✅ Field validation with helpful error messages
✅ Easy to add new shitot without API changes

## Next Steps

Phase 2 (Zmanim class integration) will:
1. Add `config: ZmanimConfig | None = None` parameter
2. Use `calculation_base` to determine how proportional times are calculated
3. Use specific tzait values for weekday vs fast vs Shabbat
4. Maintain full backward compatibility

## Files Modified

- `hdate/zmanim_config.py` - All the changes above
- `examples/zmanim_shitot_examples.py` - Updated examples
- `CONFIGURATION_QUICK_REFERENCE.md` - New quick reference
- `hdate/__init__.py` - Exports updated

## Conclusion

The refined API now properly addresses:
1. **Fast day calculations** - Different tzait for different occasions
2. **Calculation base distinction** - GRA vs MGA vs others affects multiple zmanim
3. **Pythonic design** - Flexible `**kwargs` approach scales to all fields
4. **Real-world use cases** - Each setting maps to actual community practices
5. **Clear validation** - Users get helpful error messages for typos

The configuration system is now more complete and better reflects actual halachic practice!
