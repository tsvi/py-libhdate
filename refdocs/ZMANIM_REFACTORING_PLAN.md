# Zmanim Refactoring Plan: Supporting Multiple Shitot

## Executive Summary

This document outlines the plan to add comprehensive support for different Jewish halachic opinions (shitot) regarding Zmanim calculations in py-libhdate. This addresses the primary limitation of the Home Assistant Jewish Calendar integration and provides users with fine-grained control over zmanim calculations based on their community's minhagim.

## Problem Statement

**Current State**:
- py-libhdate supports only hardcoded calculation methods for most zmanim
- Users can only customize `candle_lighting_offset` and `havdalah_offset`
- Different communities (Ashkenazi, Sephardic, Chabad, Jerusalem-based, etc.) cannot configure their preferred calculation methods
- Home Assistant integration users (649+ active installations) cannot follow their rabbi's specific opinions

**Impact**:
- Home Assistant integration includes disclaimer: "we do not take any responsibility for your religious reliance"
- Users cannot customize calculations to match their community's practices
- Library doesn't expose the variety of halachic options available

## Research Findings Summary

### Major Authorities & Shitot
1. **Gra (Vilna Gaon)** - Lithuanian standard, 19 minutes or degree-based
2. **Magen Avraham (MA)** - Stringent method, 72 minutes
3. **Chazon Ish** - Modern Lithuanian standard
4. **Baal HaTanya** - Chabad tradition
5. **Modern authorities** - Rav Feinstein, Rav Shlomo Zalman Auerbach, etc.

### Key Zmanim with Calculation Variations
- **Alot HaShachar** (dawn): 16.1°, 19 min, 72 min, 90 min
- **Sof Zman Shema**: GRA method vs MA method (proportional day)
- **Sof Zman Tfilla**: GRA method vs MA method
- **Tzait HaKochavim** (stars): 8.5°, 42 min, 45 min, 50 min, 72 min
- **Havdalah**: 40 min, 42 min, 50 min, 72 min, 8.5°

### Real-World Use Cases from Home Assistant
- Jerusalem users need 20/30/40 minute variants (not just 18)
- Different communities need GRA vs MA methods
- Sephardic vs Ashkenazi customs differ
- Users want to follow their specific rabbi's opinions

## Proposed API Design

### Phase 1: Configuration Objects + Enums (Initial Release)

#### 1. **ZmanimOpinion Enum**
Defines available calculation methods for each zman.

```python
from enum import Enum

class AlotHashacharOpinion(Enum):
    """Calculation methods for Alot HaShachar (dawn)."""
    DEGREE_16_1 = "16.1_degrees"      # Standard astronomical
    MINUTES_72 = "72_minutes"         # Magen Avraham standard
    MINUTES_90 = "90_minutes"         # Pre-dawn standard
    DAWN_MISHNAH_BERURAH = "dawn_mishnah_berurah"

class ShemaOpinion(Enum):
    """Calculation methods for Sof Zman Shema."""
    GRA = "gra"              # Vilna Gaon method (1/3 day)
    MGA = "mga"              # Magen Avraham method (1/3 light hours)

class TzaitHaKochavimOpinion(Enum):
    """Calculation methods for Tzait HaKochavim (three stars)."""
    DEGREE_8_5 = "8.5_degrees"
    MINUTES_40 = "40_minutes"
    MINUTES_42 = "42_minutes"
    MINUTES_50 = "50_minutes"
    MINUTES_72 = "72_minutes"

# ... More enums for other zmanim
```

#### 2. **ZmanimConfig Dataclass**
Configuration object that users pass to Zmanim constructor.

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ZmanimConfig:
    """Configuration for zmanim calculation methods."""
    
    alot_hashachar: Optional[AlotHashacharOpinion] = None
    misheyakir: Optional[str] = None
    shema: Optional[ShemaOpinion] = None
    tefilla: Optional[ShemaOpinion] = None
    chatzot: Optional[str] = None
    mincha_gedola: Optional[str] = None
    mincha_ketana: Optional[ShemaOpinion] = None
    plag_hamincha: Optional[str] = None
    tzait_hakochavim: Optional[TzaitHaKochavimOpinion] = None
    tzait_shabbat: Optional[TzaitHaKochavimOpinion] = None
    
    # If None, uses library defaults (which are well-documented)
    # If set, uses the specified opinion
```

#### 3. **ZmanimPresets Class**
Pre-configured opinions for common communities.

```python
class ZmanimPresets:
    """Pre-configured zmanim for common communities."""
    
    @staticmethod
    def gra_standard() -> ZmanimConfig:
        """Vilna Gaon standard (Ashkenazi, Lithuanian)."""
        return ZmanimConfig(
            alot_hashachar=AlotHashacharOpinion.DEGREE_16_1,
            shema=ShemaOpinion.GRA,
            tefilla=ShemaOpinion.GRA,
            tzait_hakochavim=TzaitHaKochavimOpinion.DEGREE_8_5,
        )
    
    @staticmethod
    def mga_standard() -> ZmanimConfig:
        """Magen Avraham standard (more stringent)."""
        return ZmanimConfig(
            alot_hashachar=AlotHashacharOpinion.MINUTES_72,
            shema=ShemaOpinion.MGA,
            tefilla=ShemaOpinion.MGA,
            tzait_hakochavim=TzaitHaKochavimOpinion.MINUTES_72,
        )
    
    @staticmethod
    def jerusalem_mainstream() -> ZmanimConfig:
        """Common Jerusalem custom."""
        return ZmanimConfig(
            # Jerusalem-specific settings
        )
    
    # ... More presets
```

#### 4. **Enhanced Zmanim Constructor**
```python
@dataclass
class Zmanim:
    date: dt.date = field(default_factory=dt.date.today)
    location: Location = field(default_factory=Location)
    candle_lighting_offset: int = 18
    havdalah_offset: int = 0
    config: Optional[ZmanimConfig] = None  # NEW: Configuration
    
    def __post_init__(self) -> None:
        # Use config if provided, otherwise use defaults
        if self.config is None:
            self.config = ZmanimConfig()  # Defaults
```

### Phase 2: Factory Methods (Optional, Later Release)

```python
class ZmanimFactory:
    """Factory for creating Zmanim with predefined configurations."""
    
    @staticmethod
    def create_gra(date: dt.date, location: Location) -> Zmanim:
        """Create Zmanim using GRA standard."""
        return Zmanim(
            date=date,
            location=location,
            config=ZmanimPresets.gra_standard()
        )
```

### Phase 3: User-Extensible Plugin System (Future)

Allow users to define custom opinions without modifying library code.

## Implementation Steps

### Step 1: Create New Configuration Module
- File: `hdate/zmanim_config.py`
- Contains: Enums, dataclasses, presets
- Documentation: Halachic sources for each opinion

### Step 2: Refactor Zmanim Class
- Add `config` parameter to constructor
- Modify `_get_utc_sun_time_deg()` to accept configuration
- Modify `zmanim` property to apply configured opinions
- Maintain backward compatibility (config defaults to library's current behavior)

### Step 3: Create Examples Module
- File: `examples/zmanim_shitot_examples.py`
- Demonstrates:
  - Using presets
  - Customizing individual opinions
  - Creating community-specific configurations
  - Integration with Home Assistant

### Step 4: Documentation
- Update zmanim docstrings with opinion definitions
- Add section to README explaining available opinions
- Document each opinion's halachic source

### Step 5: Testing
- Unit tests for each opinion
- Integration tests for combinations
- Verify backward compatibility

## Backward Compatibility Strategy

✅ **No breaking changes**
- Current code continues to work unchanged
- `config` parameter is optional
- Default config matches current behavior
- Existing Home Assistant integration works without changes
- Home Assistant can gradually adopt new features

Example:
```python
# Old code still works exactly the same:
zmanim = Zmanim(date=date, location=location, candle_lighting_offset=18)

# New code can specify opinions:
config = ZmanimConfig(
    alot_hashachar=AlotHashacharOpinion.MINUTES_72,
    tzait_hakochavim=TzaitHaKochavimOpinion.MINUTES_72,
)
zmanim = Zmanim(date=date, location=location, config=config)
```

## Benefits

### For Users
- Choose calculation methods matching their community's minhagim
- No longer bound to library's default opinions
- Can follow specific rabbi's prescriptions
- Granular control over each zman

### For Home Assistant Integration
- Users can select their community's calculation method in config
- Can provide presets in configuration dropdown
- Can remove or soften the disclaimer
- Significantly increases value of integration

### For Library Maintainers
- Clear, extensible architecture for adding new opinions
- Centralized place to document halachic sources
- Easy to add new shitot as user needs arise
- Better serves diverse Jewish communities

## Timeline

| Phase | Effort | Timeline |
|-------|--------|----------|
| Phase 1 (Config Objects + Enums) | 2-3 weeks | 2 weeks of development |
| Phase 2 (Factory Methods) | 1 week | Optional, future |
| Phase 3 (Plugin System) | 2-3 weeks | Future, only if needed |

## Success Criteria

✅ Support for 10+ major calculation methods per zman
✅ 3-5 preset configurations for common communities  
✅ Zero breaking changes for existing code
✅ Clear halachic source documentation for each opinion
✅ Examples demonstrating all major features
✅ Home Assistant integration can immediately use new features

## Files to Create/Modify

### New Files
- `hdate/zmanim_config.py` - Configuration classes and enums
- `examples/zmanim_shitot_examples.py` - Usage examples

### Modified Files
- `hdate/zmanim.py` - Add config parameter, refactor calculation logic
- `hdate/__init__.py` - Export new classes
- `tests/test_zmanim.py` - Add tests for new functionality
- `README.rst` - Document new features
- `docs/` - Add configuration guide

## Integration with Home Assistant

Once implemented, Home Assistant can:

```python
# In config flow:
async def async_step_user(self, user_input=None):
    if user_input is not None:
        preset = user_input.get("zmanim_preset", "gra_standard")
        from hdate.zmanim_config import ZmanimPresets
        config = getattr(ZmanimPresets, preset)()
        # Store in hass.data
```

This makes it easy for Home Assistant users to select their community's zmanim calculation method!

## Open Questions

1. Should `config` be a dataclass or use a different structure?
2. How granular should enum options be? (individual opinions vs grouped methods)
3. Should we support locale-specific defaults? (e.g., default to Jerusalem settings for Jerusalem)
4. How should documentation be structured? (separate file, docstrings, examples)

## Next Steps

1. ✅ Research phase complete (this document)
2. ⏳ Create `zmanim_config.py` with enums and dataclasses
3. ⏳ Refactor `zmanim.py` to use config
4. ⏳ Create comprehensive examples
5. ⏳ Update documentation
6. ⏳ Add tests
7. ⏳ Integration phase with Home Assistant
