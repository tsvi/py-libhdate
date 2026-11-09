# Home Assistant Jewish Calendar Integration - API Analysis

## Integration Overview

**Repository**: https://github.com/home-assistant/core/tree/main/homeassistant/components/jewish_calendar

**Integration Name**: `jewish_calendar`

**Documentation**: https://www.home-assistant.io/integrations/jewish_calendar/

**Integration Author**: @tsvi (You are the integration owner!)

**Status**: Core integration in Home Assistant, used by **649 active installations**

**IoT Classification**: Calculated (no hardware required)

## Current py-libhdate Usage

### How Zmanim is Instantiated

The integration creates Zmanim objects in the coordinator:

```python
# From coordinator.py
def make_zmanim(self, date: dt.date) -> Zmanim:
    """Create a Zmanim object."""
    return Zmanim(
        date=date,
        location=self.data.location,
        candle_lighting_offset=self.data.candle_lighting_offset,
        havdalah_offset=self.data.havdalah_offset,
    )
```

**Key Observations:**
1. **Only 4 parameters passed to Zmanim**: date, location, candle_lighting_offset, havdalah_offset
2. **No method/calculation customization**: Users cannot choose Shitot for any zmanim calculations
3. **Hardcoded defaults**: All zmanim calculations use whatever defaults are in py-libhdate

### Configuration Data Flow

```python
# From __init__.py - async_setup_entry
language = config_entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
diaspora = config_entry.data.get(CONF_DIASPORA, DEFAULT_DIASPORA)
candle_lighting_offset = config_entry.options.get(
    CONF_CANDLE_LIGHT_MINUTES, DEFAULT_CANDLE_LIGHT  # Default: 18
)
havdalah_offset = config_entry.options.get(
    CONF_HAVDALAH_OFFSET_MINUTES, DEFAULT_HAVDALAH_OFFSET_MINUTES  # Default: 0
)

location = Location(
    name=hass.config.location_name,
    diaspora=diaspora,
    latitude=config_entry.data.get(CONF_LATITUDE, hass.config.latitude),
    longitude=config_entry.data.get(CONF_LONGITUDE, hass.config.longitude),
    altitude=config_entry.data.get(CONF_ELEVATION, hass.config.elevation),
    timezone=config_entry.data.get(CONF_TIME_ZONE, hass.config.time_zone),
)
```

## Configuration Options Available to Users

### Initial Setup (Config Entry Data)
- **Language**: Hebrew or English
- **Diaspora**: True/False
- **Location**: Latitude/Longitude
- **Elevation**: Altitude
- **Time Zone**: Timezone

### Advanced Options (Config Entry Options - Modifiable)
- **Candle Lighting Minutes Before Sunset**: Integer (default: 18)
  - In Israel: typically 20, 30, or 40 depending on location
  - Outside Israel: customarily 18 or 24
- **Havdalah Minutes After Sunset**: Integer (default: 0)
  - When set to 0: havdalah calculated as sun 8.5 degrees below horizon
  - When set to non-zero: static offset from sunset

## Sensors Exposed to Users

### Time Sensors (Using Zmanim)
All of these are **timestamp sensors** that users can use in automations:

**Enabled by Default:**
- `netz_hachama` - Sunrise (הנץ החמה)
- `shkia` - Sunset (שקיעה)
- `upcoming_candle_lighting` - Next candle lighting (Shabbat OR Yom Tov)
- `upcoming_havdalah` - Next havdalah (Shabbat OR Yom Tov)

**Disabled by Default** (users must enable):
- `alot_hashachar` - First light of dawn (עלות השחר)
- `talit_and_tefillin` - Earliest time for tallit and tefillin (משיכיר)
- `sof_zman_shema_gra` - Latest Shema (GR"A)
- `sof_zman_shema_mga` - Latest Shema (MG"A)
- `sof_zman_tfilla_gra` - Latest Tefilla (GR"A)
- `sof_zman_tfilla_mga` - Latest Tefilla (MG"A)
- `chatzot_hayom` - Midday (חצות היום)
- `mincha_gedola` - Earliest Mincha (מנחה גדולה)
- `mincha_ketana` - Preferable Mincha (מנחה קטנה)
- `plag_hamincha` - Plag Hamincha (פלג המנחה)
- `tset_hakohavim_tsom` - Stars for fast days (צאת הכוכבים)
- `tset_hakohavim_shabbat` - Stars for Shabbat
- `upcoming_shabbat_candle_lighting` - Shabbat-specific candle lighting
- `upcoming_shabbat_havdalah` - Shabbat-specific havdalah

### Binary Sensors
- `issur_melacha_in_effect` - Currently Shabbat or Yom Tov (boolean)
- `erev_shabbat_hag` - Upcoming Shabbat or Hag (boolean)
- `motzei_shabbat_hag` - Shabbat or Hag has ended (boolean)

### Data Sensors
- `date` - Hebrew date
- `weekly_portion` - Parshat Hashavua
- `holiday` - Current holiday
- `omer_count` - Day of Omer
- `daf_yomi` - Daf Yomi page

## Pain Points & Limitations

### 1. **No Zmanim Calculation Customization**

**Current Limitation**: Users cannot choose which shita (rabbinic opinion) to use for any zmanim.

**Evidence from Code**:
```python
# The integration has NO WAY to pass calculation methods to Zmanim
# Users are stuck with whatever defaults py-libhdate uses internally
```

**Real-World Impact**:
- User in Jerusalem wants to use different minyan times than another user
- Sephardic vs Ashkenazi communities have different customs for zmanim
- Different cities have different minhagim for candle lighting offset
- No way to accommodate different rabbinic opinions

### 2. **Havdalah Calculation is Either/Or**

**Current Implementation**:
```python
# When havdalah_offset = 0: Uses 8.5 degrees below horizon
# When havdalah_offset != 0: Uses static offset from sunset
```

**Problem**: 
- No way to specify degrees other than 8.5
- No way to use different calculation methods (e.g., 72 minutes, 42 minutes)
- Different communities use different standards

### 3. **Candle Lighting is Only Fixed Offset**

**Current Implementation**:
- Only supports "X minutes before sunset"
- Default is 18 minutes

**Missing**:
- Some communities use different standards
- Jerusalem has multiple customs (20, 30, 40 minutes)
- No support for alternative calculations

### 4. **Disclaimer in Documentation**

From the Home Assistant docs:
> **Note**: Due to the variety of rabbinic opinions on calculating the different times, we do not take any responsibility for your religious reliance upon these calculations.

**This is because**: The integration provides NO way for users to choose which rabbinic opinion to follow!

## Feature Requests & Issues

Based on the GitHub search and documentation:

### Potential User Needs (Not Currently Supported)

1. **Calculation Method Selection**
   - "I need to use the 72-minute zman for alot hashachar"
   - "My community follows the MG"A for all zmanim"
   - "I want havdalah at 72 minutes, not 8.5 degrees"

2. **Custom Zmanim**
   - "I need shaah zmanit (halachic hour) calculations"
   - "I want to create automation based on Plag Hamincha but using different shita"

3. **Regional Variations**
   - "In Jerusalem we use 40 minutes before sunset"
   - "My rabbi says to use different calculation for winter vs summer"

## Code Architecture Analysis

### Coordinator Pattern
```python
class JewishCalendarUpdateCoordinator(DataUpdateCoordinator[JewishCalendarData]):
    """Data update coordinator class for Jewish calendar."""
    
    def make_zmanim(self, date: dt.date) -> Zmanim:
        """Create a Zmanim object."""
        return Zmanim(
            date=date,
            location=self.data.location,
            candle_lighting_offset=self.data.candle_lighting_offset,
            havdalah_offset=self.data.havdalah_offset,
        )
```

### Sensor Access Pattern
```python
# Sensors access zmanim through coordinator
@property
def native_value(self) -> dt.datetime | None:
    """Return the state of the sensor."""
    if self.entity_description.value_fn is None:
        return self.coordinator.zmanim.zmanim[self.entity_description.key].local
    return self.entity_description.value_fn(
        self.get_dateinfo(), self.coordinator.make_zmanim
    )
```

**Key Insight**: Sensors call `coordinator.make_zmanim()` to create Zmanim objects for different dates (like upcoming Shabbat). Each call creates a new Zmanim instance.

## How py-libhdate API Could Better Serve This Integration

### 1. **Expose Calculation Options in Zmanim Constructor**

**Current API Problem**:
```python
# Users can only do this:
zmanim = Zmanim(
    date=date,
    location=location,
    candle_lighting_offset=18,
    havdalah_offset=0
)
```

**What Integration Needs**:
```python
# Users should be able to do this:
zmanim = Zmanim(
    date=date,
    location=location,
    candle_lighting_offset=18,
    havdalah_offset=0,
    # NEW PARAMETERS NEEDED:
    alot_hashachar_method="16.1_degrees",  # or "72_minutes", "90_minutes", etc.
    misheyakir_method="10.2_degrees",      # or specific shita
    shema_method="gra",                     # or "mga"
    tefilla_method="gra",                   # or "mga"
    tzait_method="8.5_degrees",             # or "42_minutes", "72_minutes"
    # ... etc for each zman
)
```

### 2. **Provide Enumeration of Available Methods**

**What Integration Needs**:
```python
from hdate.zmanim import ZmanimMethods, AlotHashacharMethod

# So users can select from dropdown in config flow:
available_alot_methods = AlotHashacharMethod.list_options()
# Returns: ["16.1_degrees", "72_minutes", "90_minutes", "dawn_mishnah_berurah"]
```

### 3. **Preset Configurations for Common Customs**

**What Integration Needs**:
```python
from hdate.zmanim import ZmanimPresets

# Quick presets for common communities:
zmanim = Zmanim(
    date=date,
    location=location,
    preset=ZmanimPresets.JERUSALEM_MAINSTREAM,
    # or: ZmanimPresets.SEPHARDIC_STANDARD
    # or: ZmanimPresets.ASHKENAZI_GRA
    # or: ZmanimPresets.ASHKENAZI_MGA
)
```

### 4. **Better Documentation of Defaults**

**Current Problem**: Integration users don't know what calculation methods are being used!

**Solution**: Each zman should document:
- What method is used by default
- What alternatives are available
- Rabbinic source for each method

### 5. **Flexible Havdalah Calculation**

**Current Limitation**:
```python
# Only two modes: degrees (when offset=0) or fixed offset (when offset!=0)
```

**What Integration Needs**:
```python
zmanim = Zmanim(
    date=date,
    location=location,
    havdalah_calculation={
        "method": "fixed_minutes",  # or "degrees", "seasonal"
        "value": 42,  # minutes or degrees depending on method
    }
)
```

## Recommendations for py-libhdate API Enhancement

### Priority 1: Add Configuration to Zmanim Constructor

```python
class Zmanim:
    def __init__(
        self,
        date: dt.date,
        location: Location,
        candle_lighting_offset: int = 18,
        havdalah_offset: int = 0,
        # NEW: Calculation method configuration
        calculation_config: Optional[ZmanimCalculationConfig] = None,
    ):
        """
        Initialize Zmanim with optional calculation configuration.
        
        Args:
            calculation_config: Optional configuration for calculation methods.
                               If None, uses library defaults.
        """
```

### Priority 2: Create Configuration Classes

```python
@dataclass
class ZmanimCalculationConfig:
    """Configuration for zmanim calculation methods."""
    
    alot_hashachar: Optional[str] = None  # e.g., "16.1_degrees", "72_minutes"
    misheyakir: Optional[str] = None
    shema_gra: Optional[str] = None
    shema_mga: Optional[str] = None
    tefilla_gra: Optional[str] = None
    tefilla_mga: Optional[str] = None
    chatzot: Optional[str] = None
    mincha_gedola: Optional[str] = None
    mincha_ketana: Optional[str] = None
    plag_hamincha: Optional[str] = None
    tzait_hakochavim: Optional[str] = None
    tzait_shabbat: Optional[str] = None
    
    @classmethod
    def from_preset(cls, preset: str) -> "ZmanimCalculationConfig":
        """Create config from named preset."""
        presets = {
            "gra": cls(shema_gra="gra_standard", tefilla_gra="gra_standard", ...),
            "mga": cls(shema_mga="mga_standard", tefilla_mga="mga_standard", ...),
            "jerusalem": cls(alot_hashachar="16.1_degrees", ...),
        }
        return presets[preset]
```

### Priority 3: Maintain Backward Compatibility

```python
# Current code must continue to work:
zmanim = Zmanim(date=date, location=location)  # Uses defaults

# New code can specify calculations:
config = ZmanimCalculationConfig(
    alot_hashachar="72_minutes",
    tzait_hakochavim="42_minutes"
)
zmanim = Zmanim(date=date, location=location, calculation_config=config)
```

### Priority 4: Provide Discovery API

```python
# Let integrations discover available methods
from hdate.zmanim import get_available_methods

methods = get_available_methods()
# Returns:
# {
#     "alot_hashachar": [
#         {"id": "16.1_degrees", "name": "16.1 degrees", "source": "..."},
#         {"id": "72_minutes", "name": "72 minutes", "source": "..."},
#     ],
#     ...
# }
```

## Impact on Home Assistant Integration

### What This Would Enable

1. **New Config Flow Options**:
   ```yaml
   # In Home Assistant configuration
   jewish_calendar:
     calculation_preset: "jerusalem_mainstream"
     # or custom:
     custom_calculations:
       alot_hashachar: "72_minutes"
       tzait_hakochavim: "42_minutes"
   ```

2. **Per-Sensor Customization**:
   - Users could create multiple sensors with different calculation methods
   - "alot_hashachar_72_minutes" and "alot_hashachar_90_minutes" side-by-side

3. **Community Templates**:
   - Share configuration templates for different communities
   - "Jerusalem-Ashkenazi.yaml", "Tel-Aviv-Sephardi.yaml"

4. **Remove Disclaimer**:
   - With user-controllable calculations, the integration can say: "You chose these methods, you're responsible"

## Summary of Real-World User Needs

Based on the integration analysis:

1. **Multi-Opinion Support**: Users need to follow their rabbi/community's specific shita
2. **Transparency**: Users want to know WHICH calculation is being used
3. **Flexibility**: Different sensors should be able to use different methods
4. **Presets**: Most users want "Jerusalem standard" or "Ashkenazi GRA" without details
5. **Advanced Options**: Power users want full control over each individual zman
6. **Documentation**: Each method needs its halachic source documented

## Current vs. Ideal API Comparison

### Current (What Integration Can Do)
```python
zmanim = Zmanim(
    date=today,
    location=location,
    candle_lighting_offset=18,
    havdalah_offset=0  # Hope the defaults are what user needs!
)
```

### Ideal (What Integration Needs)
```python
# Preset for most users:
zmanim = Zmanim(
    date=today,
    location=location,
    candle_lighting_offset=18,
    havdalah_offset=0,
    preset="gra"  # or "mga", "jerusalem", "sephardic_standard"
)

# OR full customization for advanced users:
zmanim = Zmanim(
    date=today,
    location=location,
    candle_lighting_offset=18,
    calculation_methods={
        "alot_hashachar": "72_minutes_zmanis",
        "sof_zman_shema": "mga_3_hours",
        "tzait_hakochavim": "8.5_degrees"
    }
)
```

## Action Items for py-libhdate

1. **Research Phase**: Document all current default calculation methods in code
2. **Design Phase**: Create configuration API design (as outlined above)
3. **Implementation Phase**: 
   - Add optional parameters to Zmanim
   - Create configuration classes
   - Maintain backward compatibility
4. **Documentation Phase**: Document each method with halachic sources
5. **Testing Phase**: Verify all existing tests still pass
6. **Integration Phase**: Work with Home Assistant to add config flow options

## Conclusion

The Home Assistant Jewish Calendar integration is currently **limited by py-libhdate's API**, not by the integration's design. Users have no way to customize which rabbinic opinions are used for calculations because py-libhdate doesn't expose these options in its API.

**Key Finding**: The integration would immediately benefit from a configurable Zmanim API that:
- Exposes calculation method options
- Provides preset configurations
- Maintains backward compatibility
- Documents halachic sources

This analysis provides the real-world evidence needed to prioritize the Zmanim API refactoring work.
