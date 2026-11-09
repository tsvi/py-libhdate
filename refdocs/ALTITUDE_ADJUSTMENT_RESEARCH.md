# Altitude/Elevation Effects on Sunrise and Sunset in Jewish Law

## Research Summary: Altitude Adjustment for Zmanim Calculations

**Date:** January 25, 2026  
**Context:** py-libhdate zmanim calculation system

---

## Executive Summary

Altitude (elevation) of the observer affects visible sunrise and sunset times due to geometric considerations. An observer at a higher elevation sees the sun rise earlier and set later than an observer at sea level. This research examines the halachic approaches to altitude adjustment and technical implementation options.

**Key Finding:** While the Location class includes an `altitude` field (defaulting to 754m for Jerusalem), **the current codebase does NOT apply any altitude adjustment to zmanim calculations**. This represents a potential enhancement opportunity.

---

## 1. Physical Effect of Altitude on Sunrise/Sunset

### 1.1 Geometric Explanation

When an observer is at an elevated position:
- **Sunrise occurs EARLIER** - The observer can see the sun before it crosses the mathematical horizon at sea level
- **Sunset occurs LATER** - The observer can still see the sun after it has crossed the mathematical horizon at sea level

This is due to the **dip of the horizon** - an observer at height looks down to see the horizon, which is geometrically lower than the true horizontal plane.

### 1.2 Magnitude of Effect

From research documentation (ZMANIM_SHITOT_RESEARCH.md):
- **~2 minutes difference per 1000 feet of elevation**
- Mountain locations: Earlier sunrise, later sunset
- The effect is more pronounced at higher elevations

Example:
- Sea level: Sunrise at 6:00 AM
- 3000 feet elevation: Sunrise at ~5:54 AM (6 minutes earlier)

### 1.3 Atmospheric vs. Geometric Effects

Standard sunrise/sunset calculations already include:
- **Atmospheric refraction**: ~34 arcminutes (0.567°)
- **Solar radius**: ~16 arcminutes (0.267°)
- **Combined standard**: 50 arcminutes (0.833°)

These are built into the standard 90.833° zenith angle used for sunrise/sunset.

The altitude adjustment is a **separate geometric correction** that adds to these atmospheric effects.

---

## 2. Altitude Adjustment Formulas

### 2.1 Standard Geometric Formula

The **dip angle** (in degrees) due to observer height can be calculated as:

```
dip_angle = arccos(R / (R + h))
```

Where:
- R = Earth's radius (~6371 km or 3959 miles)
- h = observer's height/elevation above sea level

**Simplified approximation** (for small heights compared to Earth radius):

```
dip_angle_degrees ≈ 1.76 * sqrt(h_meters)  # for height in meters
dip_angle_degrees ≈ 0.97 * sqrt(h_feet)    # for height in feet
```

Or in arcminutes:
```
dip_arcminutes ≈ 1.06 * sqrt(h_meters)
dip_arcminutes ≈ 0.58 * sqrt(h_feet)
```

### 2.2 Time-Based Formula

An alternative approach calculates the time adjustment directly:

```
time_adjustment_minutes ≈ 2.0 * (h_feet / 1000)
```

This is an approximation that varies slightly with latitude and season.

### 2.3 KosherJava Implementation Reference

From the KosherJava documentation comments:
- "Sea level vs. high altitude: ~2 minute difference per 1000 feet"
- KosherJava library includes `getSeaLevelSunrise()` and `getSeaLevelSunset()` methods
- Suggests elevation correction is available in that library

---

## 3. Halachic Opinions on Altitude Adjustment

### 3.1 Current State of Halachic Consensus

**Key Issue:** There is **no clear consensus** among poskim on whether altitude should affect zmanim calculations.

### 3.2 Arguments FOR Altitude Adjustment

1. **Physical Reality (Metziut)**
   - The observer truly sees sunrise earlier from an elevated position
   - Halacha generally follows observable reality
   - "What you see is what counts" principle
   
2. **Precision in Mitzvot**
   - Modern astronomical precision allows accurate calculations
   - Being machmir (stringent) with zmanim timing
   
3. **Some Modern Poskim**
   - Various contemporary authorities have addressed this
   - Particularly relevant for mountain communities

### 3.3 Arguments AGAINST Altitude Adjustment

1. **Traditional Approach**
   - Classical sources don't distinguish by altitude
   - Most traditional communities use sea-level calculations
   
2. **Practical Considerations**
   - Difference is relatively small (minutes, not hours)
   - May cause confusion if different standards are used
   
3. **Simplification Preference**
   - Using a uniform standard (sea level) for a region
   - Easier for community coordination

### 3.4 Authority-Specific Positions

**Note:** Specific documented positions by GRA, MGA, Chazon Ish, etc. on altitude adjustment are not found in the current codebase research.

However, from ZMANIM_SHITOT_RESEARCH.md:
- **GRA (Vilna Gaon)**: Based calculations on solar geometry and altitude considerations (but unclear if this refers to zenith angles or observer altitude)
- **MGA (Magen Avraham)**: Uses proportional hour calculations
- **Chazon Ish**: Uses specific degree measurements
- **None specifically documented as requiring altitude adjustment**

### 3.5 Modern Practice

From codebase analysis:
- **KosherJava**: Provides both regular and "sea level" calculations (implying altitude adjustment is optional)
- **Most online calculators**: Some ignore altitude, others include it as an option
- **Implementation varies**: No universal standard

---

## 4. Technical Implementation Approaches

### 4.1 Current py-libhdate Status

**Location Class** (hdate/location.py):
```python
@dataclass(frozen=True)
class Location:
    name: str = "Jerusalem"
    latitude: float = 31.778
    longitude: float = 35.235
    timezone: str | tzinfo = ZoneInfo("Asia/Jerusalem")
    altitude: float = 754  # ← FIELD EXISTS
    diaspora: bool = False
```

**Current Calculation** (hdate/zmanim.py):
- Uses `self.location.latitude` and `self.location.longitude`
- **Does NOT use `self.location.altitude`** in any calculation
- The altitude field is stored but ignored

### 4.2 Zenith Angle Adjustment Method

**Approach:** Modify the zenith angle based on altitude

```python
def _calculate_elevation_adjusted_zenith(self, base_zenith: float) -> float:
    """
    Adjust zenith angle for observer elevation.
    
    Formula: dip_angle = 1.76 * sqrt(altitude_meters)
    """
    if self.location.altitude <= 0:
        return base_zenith
    
    # Calculate dip angle in degrees
    dip_degrees = 1.76 * math.sqrt(self.location.altitude)
    
    # For sunrise: sun must be HIGHER (lower zenith angle)
    # For sunset: sun can be LOWER (higher zenith angle)
    # This affects both equally, so we adjust the base zenith
    
    return base_zenith - dip_degrees  # Negative dip = sun rises earlier/sets later
```

**Application:**
- Modify `_get_utc_sun_time_deg()` to accept elevation-adjusted zenith
- Apply before calculation of sunrise/sunset
- Affects all degree-based calculations

### 4.3 Time Offset Method

**Approach:** Calculate time adjustment and apply as offset

```python
def _calculate_elevation_time_offset(self, is_sunrise: bool) -> float:
    """
    Calculate time offset in minutes due to elevation.
    
    Approximate: 2 minutes per 1000 feet
    """
    if self.location.altitude <= 0:
        return 0.0
    
    # Convert meters to feet
    altitude_feet = self.location.altitude * 3.28084
    
    # Calculate offset (negative for sunrise, positive for sunset)
    offset_minutes = 2.0 * (altitude_feet / 1000.0)
    
    return -offset_minutes if is_sunrise else offset_minutes
```

**Application:**
- Apply as final adjustment after basic calculation
- Simpler but less precise
- Easier to make optional

### 4.4 Astral Library Integration

The `astral` library's `Observer` class supports elevation:

```python
astral_observer = astral.Observer(
    latitude=self.location.latitude,
    longitude=self.location.longitude,
    elevation=self.location.altitude  # ← ADD THIS
)
```

**Current code** (line 293-296 in zmanim.py):
```python
astral_observer = astral.Observer(
    latitude=self.location.latitude,
    longitude=self.location.longitude,
)  # elevation parameter is NOT provided
```

**Simple fix:** Add `elevation=self.location.altitude` parameter

---

## 5. Configuration System Integration

### 5.1 Proposed Configuration Option

Add to `ZmanimConfig`:

```python
@dataclass
class ZmanimConfig:
    # ... existing fields ...
    
    apply_elevation_adjustment: bool = False  # Default: OFF for backward compatibility
    elevation_adjustment_method: str = "geometric"  # "geometric", "time_offset", or "none"
```

### 5.2 Preset Configurations

```python
# Traditional - no altitude adjustment
gra_standard_traditional = ZmanimConfig(
    apply_elevation_adjustment=False,
    # ...
)

# Modern with altitude adjustment
gra_standard_altitude_adjusted = ZmanimConfig(
    apply_elevation_adjustment=True,
    elevation_adjustment_method="geometric",
    # ...
)
```

### 5.3 Authority-Specific Defaults

**Recommendation:** Default to NO altitude adjustment for all authorities unless specific sources indicate otherwise:
- **GRA**: No altitude adjustment (traditional)
- **MGA**: No altitude adjustment (traditional)
- **Chazon Ish**: No altitude adjustment (traditional)
- **Modern/Custom**: Optional altitude adjustment available

---

## 6. Recommendations for Implementation

### 6.1 Priority Level: MEDIUM-LOW

**Rationale:**
1. Not a halachic requirement for most authorities
2. Effect is relatively small (minutes)
3. No widespread demand documented
4. Backward compatibility concerns

### 6.2 Implementation Strategy

**Phase 1: Quick Win (If implementing astral path)**
```python
# In _get_utc_time_of_transit() method:
astral_observer = astral.Observer(
    latitude=self.location.latitude,
    longitude=self.location.longitude,
    elevation=self.location.altitude,  # Add this line
)
```

**Pros:** Simple, uses library's built-in support  
**Cons:** Only affects astral-based calculations, not NOAA algorithm path

**Phase 2: Comprehensive Implementation**
1. Add configuration option to ZmanimConfig
2. Implement zenith angle adjustment method
3. Apply consistently to both calculation paths
4. Add documentation and examples
5. Include tests for elevation effects

**Phase 3: Advanced Features**
- Add "sea level equivalent" calculation option
- Support different elevation models
- Add documentation of halachic sources

### 6.3 Backward Compatibility

**CRITICAL:** Default behavior must remain unchanged

```python
# Default: NO altitude adjustment
apply_elevation_adjustment: bool = False
```

This ensures existing users' calculations don't change unexpectedly.

### 6.4 Documentation Requirements

If implemented, document:
1. That altitude adjustment is **optional** and **not halachically required**
2. The formula used for adjustment
3. Which authorities (if any) recommend its use
4. Example: "Jerusalem at 754m vs. sea level: ~1.5 minutes difference"

---

## 7. Specific Answers to Research Questions

### Q1: How does altitude/elevation affect visible sunrise and sunset times?

**A:** Higher elevation → Earlier sunrise, Later sunset  
**Magnitude:** ~2 minutes per 1000 feet (~305 meters)  
**Formula:** dip_angle ≈ 1.76 * sqrt(altitude_meters)

### Q2: What are the different halachic opinions on altitude adjustment?

**A:** No clear consensus found. Options:
- **Traditional:** Ignore altitude, use sea-level calculations
- **Modern precision:** Apply altitude adjustment based on physical reality
- **Practical:** Most authorities don't specifically address this

### Q3: What are common altitude adjustment methods?

**A:** Two primary methods:
1. **Geometric/Zenith adjustment:** Modify zenith angle by dip_angle
2. **Time offset:** Apply ~2 min/1000 ft as post-calculation adjustment

### Q4: Do different authorities have different approaches?

**A:** No specific documented differences among GRA, MGA, Chazon Ish regarding altitude.  
Most traditional authorities didn't address this modern precision question.

### Q5: Is there a standard formula?

**A:** Yes, geometric formula:
```
dip_degrees = 1.76 * sqrt(altitude_meters)
adjusted_zenith = base_zenith - dip_degrees
```

### Q6: Should altitude adjustment be applied to zenith or as time offset?

**A:** **Zenith angle adjustment is more accurate** because:
- It's based on geometric reality
- Affects the actual solar position calculation
- Works consistently across latitudes and seasons
- Time offset is an approximation that varies by location

---

## 8. References and Sources

### 8.1 Codebase References

- `hdate/location.py` - Location class with altitude field
- `hdate/zmanim.py` - Zmanim calculation (altitude currently unused)
- `ZMANIM_SHITOT_RESEARCH.md` - Mentions elevation effects
- KosherJava project - Referenced as having elevation support

### 8.2 External References

- NOAA Solar Calculator: https://gml.noaa.gov/grad/solcalc/solareqns.PDF
- KosherJava Zmanim Project: https://www.kosherjava.com/zmanim-project/
- Astronomical Algorithms by Jean Meeus (referenced in code)
- "Using a Digital Terrain Model to Calculate Visual Sunrise and Sunset Times" (chai tables)

### 8.3 Halachic Sources

**Note:** Specific halachic sources on altitude adjustment not found in codebase.  
Recommended for future research:
- Contemporary responsa on zmanim precision
- Writings on astronomical calculations in halacha
- Modern poskim addressing mountain communities

---

## 9. Conclusion

**Current Status:** py-libhdate stores altitude but doesn't use it in calculations.

**Recommendation:** 
1. **Low priority** for immediate implementation
2. **If implemented:** Make it optional, default OFF
3. **Best approach:** Zenith angle adjustment method
4. **Quick win:** Add elevation parameter to astral Observer
5. **Document clearly:** This is an optional precision feature, not a halachic requirement

**Impact if NOT implemented:** Minimal - traditional approach is valid and widely used

**Impact if implemented:** 
- Provides option for users wanting maximum precision
- Useful for mountain communities
- Must be clearly documented as optional
