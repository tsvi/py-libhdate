# Zmanim Configuration Architecture - Final Design

## Architecture Overview

This document describes the final refactored architecture for the Zmanim configuration system, which simplifies and corrects the design to eliminate redundancy while adding missing fundamental times.

## Key Design Decisions

### 1. **CalculationMethod Enum (Not Literal)**
- **Changed from**: `Literal["gra", "mga", "baal_hatanya"]`
- **Changed to**: `Enum with GRA and MGA`
- **Rationale**: Enums provide type safety, IDE autocomplete, and explicit member documentation

```python
class CalculationMethod(Enum):
    GRA = "gra"  # Vilna Gaon - sunrise to sunset
    MGA = "mga"  # Magen Avraham - dawn to nightfall (equivalent to Baal HaTanya)
```

### 2. **Consolidated MGA and Baal HaTanya**
- **Why**: They are functionally identical for calculation purposes
- **Implementation**: 
  - Removed "baal_hatanya" as a separate option
  - If users need Baal HaTanya semantics, they use `CalculationMethod.MGA`
  - This reduces complexity without losing functionality

### 3. **Removed Redundant `sof_zman_*` Fields**
**Removed fields**:
- `sof_zman_shema_gra`
- `sof_zman_shema_mga`
- `sof_zman_tfilla_gra`
- `sof_zman_tfilla_mga`

**Why**: These are **calculated values**, not configuration:
- `sof_zman_shema` = start of day + 1/3 of day length
- `sof_zman_tfilla` = start of day + 1/3 of day length
- The calculation is determined by `calculation_method` and the fundamental times (alot/netz)
- Having them as configuration fields was architecturally unsound

**New approach**: These are calculated by the Zmanim class from:
1. `calculation_method` (determines whether we use sunrise-to-sunset or dawn-to-nightfall)
2. `alot_hashachar` (dawn time)
3. `netz_hachama` (sunrise)
4. `tzait_hakochavim` (nightfall)

### 4. **Added Fundamental Time: `netz_hachama` (Sunrise)**
- **Why**: Sunrise is a fundamental astronomical time used in calculations
- **Usage**: 
  - GRA method: Uses sunrise as the start of the halachic day
  - Basis for mincha, plag hamincha, and other afternoon calculations
  - Was missing from previous architecture

### 5. **Added `talit_and_tefillin` Time**
- **Why**: Earliest time to put on tallit and tefillin is a distinct halachic time
- **Common values**:
  - 10.2 degrees (same as misheyakir)
  - 60-90 minutes before sunrise
  - Can differ from alot_hashachar in some customs

## Final ZmanimConfig Fields

### Fundamental Calculation Method
- `calculation_method: CalculationMethod` - GRA or MGA (enum)

### Fundamental Times (Configurable)
- `alot_hashachar` - Dawn (when first light appears)
- `misheyakir` - When it becomes light enough to recognize a friend
- `netz_hachama` - Sunrise (when sun appears on horizon)
- `chatzot` - Midday/Noon
- `talit_and_tefillin` - Earliest time for tallit and tefillin
- `tzait_hakochavim` - Nightfall (stars appear) - regular days
- `tzait_fast_day` - Nightfall for fasting days (Tisha B'Av, Yom Kippur)
- `tzait_shabbat` - Nightfall for Shabbat/Yom Tov ends

### Derived Times (Calculated, Not Configurable)
These are calculated from the fundamental times above:
- `sof_zman_shema` - Latest time for Shema (calculated as 1/3 of day from day start)
- `sof_zman_tfilla` - Latest time for morning prayers (calculated as 1/3 of day from day start)
- `mincha_gedola` - Earliest Mincha (calculated as 30 minutes after chatzot)
- `mincha_ketana` - Preferred Mincha (calculated as 9.5 halachic hours from day start)
- `plag_hamincha` - 1.25 halachic hours before sunset
- `chatzot_halayla` - Midnight (exactly 12 halachic hours after sunset)

## Key Improvements

### Before (Phase 1)
```python
ZmanimConfig(
    calculation_base="gra",  # Literal string
    sof_zman_shema_gra=...,  # Redundant
    sof_zman_shema_mga=...,  # Redundant
    sof_zman_tfilla_gra=..., # Redundant
    sof_zman_tfilla_mga=..., # Redundant
    # No netz_hachama
    # No talit_and_tefillin
)
```

### After (Phase 2)
```python
ZmanimConfig(
    calculation_method=CalculationMethod.GRA,  # Enum, type-safe
    alot_hashachar=ZmanMethod(degrees=16.1),
    netz_hachama=None,  # Can configure if needed, calculated otherwise
    misheyakir=ZmanMethod(degrees=10.2),
    talit_and_tefillin=None,  # Can configure if needed
    tzait_hakochavim=ZmanMethod(degrees=8.5),
    tzait_fast_day=ZmanMethod(minutes=50),  # Can differ from regular tzait
    tzait_shabbat=ZmanMethod(minutes=50),   # Can differ from regular tzait
    # sof_zman_* are calculated from these fundamental times
)
```

## Architectural Principles

### 1. **Single Source of Truth**
- Each time is defined exactly once
- No redundancy between GRA and MGA versions of the same time
- MGA vs GRA differences are handled via `calculation_method`, not separate fields

### 2. **Fundamental vs Derived**
- **Configuration contains only fundamental times** (alot, netz, tzait, etc.)
- **Derived times are calculated** in the Zmanim class
- This makes the API simpler and more maintainable

### 3. **Flexibility for Communities**
- Users can customize any fundamental time independently
- Different values for fast days vs regular days (tzait_fast_day)
- Different values for Shabbat vs weekdays (tzait_shabbat)
- Different calculation bases (GRA vs MGA) available via enum

### 4. **Immutability**
- All configuration classes are frozen dataclasses
- Configuration objects are thread-safe and hashable
- Prevents accidental mutations

## Usage Examples

### Using Presets
```python
from hdate import ZmanimPresets, Zmanim, Location

config = ZmanimPresets.gra_standard()
location = Location(latitude=31.77, longitude=35.23)
zmanim = Zmanim(config=config, location=location)
```

### Creating Custom Configurations
```python
from hdate import create_custom_config, ZmanMethod, CalculationMethod

# Using the helper function with strings (converted to enum)
config = create_custom_config(
    calculation_method="gra",
    alot_hashachar=ZmanMethod(degrees=16.1),
    tzait_hakochavim=ZmanMethod(minutes=42),
    tzait_fast_day=ZmanMethod(minutes=50),  # More stringent for fasts
)

# Or using enum directly
config = ZmanimConfig(
    calculation_method=CalculationMethod.GRA,
    alot_hashachar=ZmanMethod(degrees=16.1),
    tzait_hakochavim=ZmanMethod(minutes=42),
)
```

### Different Fast Day Configuration
```python
config = ZmanimConfig(
    calculation_method=CalculationMethod.GRA,
    alot_hashachar=ZmanMethod(degrees=16.1),
    tzait_hakochavim=ZmanMethod(minutes=42),     # Regular weekday
    tzait_fast_day=ZmanMethod(minutes=50),       # More stringent
    tzait_shabbat=ZmanMethod(minutes=50),        # Shabbat ends later
)
```

## Validation

The architecture is validated by:
1. ✅ ZmanMethod enforces exactly one of (degrees, minutes)
2. ✅ ZmanimConfig validates calculation_method is CalculationMethod enum
3. ✅ create_custom_config validates all field names
4. ✅ create_custom_config converts string method names to enum
5. ✅ All 7 presets working correctly with new enum
6. ✅ Fast day support (separate tzait_fast_day field)
7. ✅ Shabbat support (separate tzait_shabbat field)
8. ✅ Frozen dataclasses prevent accidental mutations

## What's Not Configurable (And Why)

### `netz_hachama`, `chatzot`
- These are astronomical times rarely customized
- Available as fields but typically left as None
- Library calculates them astronomically if None

### Derived times
- Not configurable because they're derived from fundamental times
- Attempting to configure them would violate "single source of truth"
- Example: `sof_zman_shema` is always 1/3 of day from day start, can't be different

## Next Steps

1. **Phase 2: Zmanim Class Integration**
   - Modify Zmanim class to accept ZmanimConfig parameter
   - Implement calculation logic using configuration
   - Maintain backward compatibility (default to GRA standard)

2. **Testing**
   - Unit tests for configuration validation
   - Integration tests with Zmanim class
   - Tests for all 7 presets
   - Tests for custom configurations

3. **Documentation**
   - Update Home Assistant integration documentation
   - Add examples for common use cases
   - Document how to customize for specific communities

4. **Home Assistant Integration Update**
   - Enable configuration of calculation_method
   - Enable configuration of tzait_fast_day, tzait_shabbat
   - Add presets selection in integration options
