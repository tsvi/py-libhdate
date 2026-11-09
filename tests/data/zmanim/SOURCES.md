# Zmanim Reference Data Sources

This document describes available zmanim data sources for validation testing.

## Currently Implemented

### Hebcal (https://www.hebcal.com)
- **API URL**: `https://www.hebcal.com/zmanim`
- **Format**: JSON
- **Coverage**: Worldwide
- **License**: Creative Commons Attribution 4.0 International
- **Implementation**: `utils/fetch_zmanim_reference.py --source hebcal`
- **Documentation**: https://www.hebcal.com/home/195/zmanim-halachic-times-api
- **Status**: ✅ Fully working

**Available Fields**:
- `alotHaShachar` → `alot_hashachar`
- `misheyakir` → `misheyakir`
- `sunrise` → `netz_hachama`
- `sofZmanShma` → `sof_zman_shema`
- `sofZmanTfilla` → `sof_zman_tfilla`
- `chatzot` → `chatzot_hayom`
- `chatzotNight` → `chatzot_halayla`
- `minchaGedola` → `mincha_gedola`
- `minchaKetana` → `mincha_ketana`
- `plagHaMincha` → `plag_hamincha`
- `sunset` → `shkia`
- `tzeit85deg` → `tset_hakohavim`
- And many more variant calculations

**Known Issues**:
1. **Day Boundary Differences**:
   - `chatzot_halayla`: Hebcal reports midnight for the night that *starts* the day,
     py-libhdate reports it for the night that *ends* the day (24 hours difference).
   - For southern hemisphere or locations where local date != UTC date: Times may be
     reported for different calendar days (currently excluded from tests).

2. **Calculation Method Differences**:
   - `misheyakir`: Hebcal uses different degree calculations (varies by location/season)
   - Tolerance needs to be adjusted per location

---

## Implemented Sources

### MyZmanim (https://www.myzmanim.com)
- **Website**: `https://www.myzmanim.com`
- **Format**: HTML (JavaScript-rendered)
- **Coverage**: Worldwide
- **Implementation**: `utils/fetch_zmanim_reference.py --source myzmanim`
- **Requirements**: `pip install playwright && playwright install chromium`
- **Status**: ✅ Working (TODAY only - free tier limitation)

**Limitation**: MyZmanim requires a paid subscription to access historical or future dates.
The free tier only provides zmanim for the current day.

**Available Fields**:
- `Talis` → `misheyakir`
- `Sunrise` → `netz_hachama`
- `Sunset` → `shkia`
- `Midday` → `chatzot_hayom`
- `Shema` → `sof_zman_shema`
- `Shchrs` → `sof_zman_tfilla`
- `Nightfall` → `tset_hakohavim`
- `Candles` → `candle_lighting`

**Notes**:
- Requires playwright for JavaScript rendering
- Searches by location name
- Only works for today's date without subscription

---

### Skyview / Chazon Shamayim (https://skyview2020.co.il)
- **API URL**: `https://skyview2020.co.il/send-ajax.php`
- **Format**: JSON REST API
- **Coverage**: Israel only
- **Implementation**: `utils/fetch_zmanim_reference.py --source skyview`
- **Requirements**: None (uses standard library)
- **Status**: ✅ Working for Israeli locations
- **Detailed Methods**: See [/refdocs/SKYVIEW_ZMANIM_METHODS.md](/refdocs/SKYVIEW_ZMANIM_METHODS.md)

**API Parameters**:
- `LocName`: Hebrew city name (e.g., ירושלים)
- `Region`: "Israel"
- `Method`: "חזון_שמים" (Ashkenazi) or "ספרדי" (Sephardic)
- `year`, `month`, `day`: Hebrew date

**Available Fields**:
- `עלות השחר א` → `alot_hashachar` (90 min, stringent)
- `עלות השחר ב` → `alot_hashachar_72` (72 min)
- `טלית ותפילין` → `misheyakir`
- `זריחה מישורית` → `netz_hachama`
- `ק״ש גר״א` → `sof_zman_shema`
- `תפילה גר״א` → `sof_zman_tfilla`
- `ק״ש מג״א` → `sof_zman_shema_mga`
- `תפילה מג״א` → `sof_zman_tfilla_mga`
- `חצות` → `chatzot_hayom`
- `מנחה גדולה` → `mincha_gedola`
- `מנחה קטנה` → `mincha_ketana`
- `פלג המנחה` → `plag_hamincha`
- `שקיעה` → `shkia`
- `הדלקת נרות` → `candle_lighting`
- `מוצאי שבת` → `tset_hakohavim`
- `מוצ״ש ר״ת` → `tzait_rabbeinu_tam`

**Supported Locations** (add Hebrew names to manifest):
- Jerusalem → ירושלים
- Tel Aviv → תל_אביב
- Haifa → חיפה
- And more (see SKYVIEW_CITIES in scraper)

**Key Calculation Methods**:
| Zman | Ashkenazi | Sephardic |
|------|-----------|-----------|
| Alot HaShachar | 16.013° (72 min) or 19.75° (90 min) | 72 zmaniyot minutes |
| Misheyakir | 11.5° (10.5° some locations) | 66 zmaniyot minutes |
| Tzait Shabbat | 8.5° | 30 fixed minutes |
| Tzait Fast Day | 6.45° | 20 fixed minutes |

---

## Blocked Sources

### Chabad.org (https://www.chabad.org/calendar/zmanim_cdo)
- **Website**: `https://www.chabad.org/calendar/zmanim_cdo`
- **Coverage**: Worldwide
- **Status**: ❌ Blocked by Cloudflare bot protection

Chabad.org uses Cloudflare's bot protection which blocks automated scraping.
Headless browsers are detected and presented with a challenge page.

**Potential workarounds** (not implemented):
- Use browser automation with human interaction
- Find an undocumented API endpoint
- Use a CAPTCHA-solving service (not recommended)

---

## Potential Future Sources

### KosherJava / Zmanim Library
- **GitHub**: https://github.com/KosherJava/zmanim
- **Status**: Not implemented
- **Language**: Java
- **Notes**: Well-maintained, could potentially run via Jython or compare outputs

### Ohr Somayach Zmanim
- **URL**: https://ohr.edu/explore_Judaism/zmanim
- **Status**: Not yet implemented
- **Format**: HTML
- **Notes**: Limited locations

### US Naval Observatory
- **URL**: https://aa.usno.navy.mil/data/RS_OneDay
- **Status**: Not yet implemented
- **Format**: HTML/JSON for sunrise/sunset only
- **Notes**: Astronomical data only, no halachic times

## Implementation Guidelines

### Adding a New Source

1. **Create a fetcher function** in `utils/fetch_zmanim_reference.py`:
   ```python
   def _fetch_source_name(location: dict[str, Any], date_str: str) -> dict[str, str]:
       # Fetch and map fields
       pass
   ```

2. **Update manifest** to include source selection:
   ```json
   {
     "sources": ["hebcal", "new_source"],
     ...
   }
   ```

3. **Handle field mapping**: Map source field names to py-libhdate field names

4. **Document differences**: Add to this file and test exclusions as needed

5. **Add reference test**: Update `tests/test_zmanim_reference.py`

### Handling Discrepancies

When adding new sources, document calculation differences:

1. **Excluded fields**: Add to `EXCLUDED_ZMANIM` in test file
2. **Tolerance adjustments**: Update `tolerance_minutes` in manifest per location
3. **Source-specific notes**: Document in this file

## Comparison Strategy

### Multi-Source Validation
When bug reports come in:

1. Add location/date to manifest
2. Fetch from all available sources
3. Store separate JSON files per source
4. Compare py-libhdate against consensus or specific authority
5. Document any intentional deviations

### Tolerance Guidelines

- **Normal locations**: 3 minutes default
- **High latitudes (>55°)**: 7+ minutes (astronomical calculation differences)
- **Southern hemisphere**: Check for day-boundary issues
- **Without astral library**: 5+ minutes (fallback calculations less precise)

## License Compliance

- **Hebcal**: CC-BY-4.0 - Attribution required
- Always give credit to data sources in documentation and test outputs
- Check license for any new sources before implementation
