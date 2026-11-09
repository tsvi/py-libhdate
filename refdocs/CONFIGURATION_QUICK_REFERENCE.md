# Zmanim Configuration Quick Reference

## Installation
```python
from hdate.zmanim_config import (
    ZmanMethod,
    ZmanimConfig,
    ZmanimPresets,
    ZmanMethodPresets,
    create_custom_config,
)
```

## Basic Usage

### Use a Preset Configuration
```python
# GRA (Vilna Gaon) - Most common Ashkenazi
config = ZmanimPresets.gra_standard()

# Magen Avraham - More stringent
config = ZmanimPresets.mga_standard()

# Jerusalem Ashkenazi
config = ZmanimPresets.jerusalem_standard()

# Israeli standard (42 minutes)
config = ZmanimPresets.israel_standard()

# Sephardic (50 minutes)
config = ZmanimPresets.sephardic_standard()
```

## Key Improvements

### 1. Calculation Base (GRA vs MGA)
```python
# GRA: sunrise to sunset
config = ZmanimPresets.gra_standard()

# MGA: dawn (alot) to nightfall (tzait)
config = ZmanimPresets.mga_standard()

# Or create custom with specific base:
config = create_custom_config(
    calculation_base="mga",
    alot_hashachar=ZmanMethod(minutes=72),
    tzait_hakochavim=ZmanMethod(minutes=72),
)
```

### 2. Fast Day vs Weekday vs Shabbat
```python
config = create_custom_config(
    calculation_base="gra",
    # Regular weekday nightfall
    tzait_hakochavim=ZmanMethod(minutes=42),
    # Fasting days (Tisha B'Av, Yom Kippur)
    tzait_fast_day=ZmanMethod(minutes=50),
    # Shabbat/Yom Tov ends (more stringent)
    tzait_shabbat=ZmanMethod(minutes=50),
)
```

### 3. Pythonic Helper Function
```python
# Now accepts any valid field - very flexible!
config = create_custom_config(
    calculation_base="mga",
    alot_hashachar=ZmanMethod(degrees=16.1),
    tzait_hakochavim=ZmanMethod(minutes=42),
    tzait_fast_day=ZmanMethod(minutes=50),
    tzait_shabbat=ZmanMethod(minutes=50),
    # ... any other field
)

# Invalid fields raise TypeError with clear message
try:
    bad = create_custom_config(
        invalid_field=ZmanMethod(degrees=16.1)
    )
except TypeError as e:
    print(e)  # Tells you which fields are valid
```

## Available Presets

### Alot HaShachar (Dawn)
```python
ZmanMethodPresets.ALOT_16_1_DEGREES   # GRA standard
ZmanMethodPresets.ALOT_72_MINUTES     # Magen Avraham
ZmanMethodPresets.ALOT_90_MINUTES     # Stringent
ZmanMethodPresets.ALOT_19_8_DEGREES   # Alternative
```

### Tzait HaKochavim (Nightfall)
```python
ZmanMethodPresets.TZAIT_8_5_DEGREES   # GRA (3 medium stars)
ZmanMethodPresets.TZAIT_40_MINUTES    # Jerusalem
ZmanMethodPresets.TZAIT_42_MINUTES    # Israeli standard
ZmanMethodPresets.TZAIT_50_MINUTES    # Mishnah Berurah
ZmanMethodPresets.TZAIT_72_MINUTES    # Magen Avraham
```

## Advanced Usage

### Modify a Preset
```python
from dataclasses import replace

base = ZmanimPresets.gra_standard()
modified = replace(
    base,
    tzait_fast_day=ZmanMethod(minutes=60),
    tzait_shabbat=ZmanMethod(minutes=50),
)
```

### Community-Specific
```python
# GRA with 50-minute nightfall for Shabbat
config = create_custom_config(
    calculation_base="gra",
    alot_hashachar=ZmanMethodPresets.ALOT_16_1_DEGREES,
    tzait_hakochavim=ZmanMethodPresets.TZAIT_8_5_DEGREES,
    tzait_fast_day=ZmanMethodPresets.TZAIT_50_MINUTES,
    tzait_shabbat=ZmanMethodPresets.TZAIT_50_MINUTES,
)

# MGA stringent
config = create_custom_config(
    calculation_base="mga",
    alot_hashachar=ZmanMethodPresets.ALOT_72_MINUTES,
    tzait_hakochavim=ZmanMethodPresets.TZAIT_72_MINUTES,
    tzait_fast_day=ZmanMethodPresets.TZAIT_72_MINUTES,
    tzait_shabbat=ZmanMethodPresets.TZAIT_72_MINUTES,
)

# Rabeinu Tam (very late)
config = ZmanimPresets.rabeinu_tam()
```

## Integration with Zmanim Class (Planned)

```python
from hdate import Zmanim, Location
from hdate.zmanim_config import ZmanimPresets
import datetime as dt

location = Location(
    latitude=40.7128,
    longitude=-74.0060,
    timezone="America/New_York",
)

config = ZmanimPresets.gra_standard()
zmanim = Zmanim(
    date=dt.date.today(),
    location=location,
    config=config,
)

print(zmanim.alot_hashachar.local)
print(zmanim.tzait_hakochavim.local)
```

## Home Assistant Integration (Planned)

```python
PRESET_OPTIONS = {
    "gra_standard": "GRA (Vilna Gaon) - Ashkenazi",
    "mga_standard": "Magen Avraham - Stringent",
    "jerusalem_standard": "Jerusalem Ashkenazi",
    "israel_standard": "Israeli Standard",
    "sephardic_standard": "Sephardic/Mizrachi",
}

user_choice = "gra_standard"
preset_fn = getattr(ZmanimPresets, user_choice)
config = preset_fn()

zmanim = Zmanim(
    date=date,
    location=location,
    config=config,
)
```

## Validation

```python
# Valid
method = ZmanMethod(degrees=16.1)   ✓
method = ZmanMethod(minutes=72)     ✓

# Invalid
method = ZmanMethod(degrees=16.1, minutes=72)  # ValueError
method = ZmanMethod()                          # ValueError
method = ZmanMethod(degrees=-16.1)             # ValueError

# Field validation in helper
config = create_custom_config(
    invalid_field=ZmanMethod(degrees=16.1)  # TypeError
)
```

## Complete Configuration Fields

```python
ZmanimConfig(
    # Calculation base (affects proportional times)
    calculation_base="gra",  # or "mga", "baal_hatanya"
    
    # Dawn and morning
    alot_hashachar=...,
    misheyakir=...,
    
    # Shema and Tfilla
    sof_zman_shema_gra=...,
    sof_zman_shema_mga=...,
    sof_zman_tfilla_gra=...,
    sof_zman_tfilla_mga=...,
    
    # Afternoon
    chatzot=...,
    mincha_gedola=...,
    mincha_ketana=...,
    plag_hamincha=...,
    
    # Evening/Night (can differ for weekday/fast/Shabbat)
    tzait_hakochavim=...,      # Regular weekday
    tzait_fast_day=...,        # Fasting days
    tzait_shabbat=...,         # Shabbat/Yom Tov
)
```

## Key Improvements Made

✅ **calculation_base** - GRA vs MGA affects all proportional times
✅ **tzait_fast_day** - Different end for fasting days
✅ **Pythonic helper** - `create_custom_config()` accepts any field
✅ **Better separation** - weekday vs fast vs Shabbat are distinct
✅ **Field validation** - Helper function validates field names

## More Examples

See `examples/zmanim_shitot_examples.py` for 20+ examples
