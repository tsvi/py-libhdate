"""Fetch external zmanim references and store as JSON.

Supported sources:
  - hebcal: REST API (default, fully working for all locations/dates)
  - myzmanim: Browser automation - TODAY only (free tier limitation)
  - chabad: BLOCKED by Cloudflare bot protection
  - skyview: REST API for Israeli locations (fully working)

Usage:
  # Hebcal (default)
  python utils/fetch_zmanim_reference.py \\
    --manifest tests/data/zmanim/manifest.json \\
    --output tests/data/zmanim/hebcal_reference.json

  # MyZmanim (requires: pip install playwright && playwright install chromium)
  python utils/fetch_zmanim_reference.py \\
    --source myzmanim \\
    --manifest tests/data/zmanim/manifest.json \\
    --output tests/data/zmanim/myzmanim_reference.json

  # Skyview (Israeli locations only)
  python utils/fetch_zmanim_reference.py \\
    --source skyview \\
    --manifest tests/data/zmanim/manifest.json \\
    --output tests/data/zmanim/skyview_reference.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

HEBCAL_BASE_URL = "https://www.hebcal.com/zmanim"
MYZMANIM_BASE_URL = "https://www.myzmanim.com"
CHABAD_BASE_URL = "https://www.chabad.org/calendar/zmanim_cdo"
SKYVIEW_API_URL = "https://skyview2020.co.il/send-ajax.php"

# Hebrew city name mappings for Skyview
SKYVIEW_CITIES = {
    "Jerusalem, IL": "ירושלים",
    "Tel Aviv, IL": "תל_אביב",
    "Haifa, IL": "חיפה",
    "Beer Sheva, IL": "באר_שבע",
    "Bnei Brak, IL": "בני_ברק",
    "Petach Tikva, IL": "פתח_תקווה",
    "Ashdod, IL": "אשדוד",
    "Netanya, IL": "נתניה",
    "Holon, IL": "חולון",
    "Ramat Gan, IL": "רמת_גן",
}

HEBCAL_TO_ZMANIM = {
    "alotHaShachar": "alot_hashachar",
    "misheyakir": "misheyakir",
    "sunrise": "netz_hachama",
    "sunset": "shkia",
    "chatzot": "chatzot_hayom",
    "sofZmanShma": "sof_zman_shema",
    "sofZmanTfilla": "sof_zman_tfilla",
    "minchaGedola": "mincha_gedola",
    "minchaKetana": "mincha_ketana",
    "plagHaMincha": "plag_hamincha",
    "tzeit85deg": "tset_hakohavim",
    "chatzotNight": "chatzot_halayla",
}

# MyZmanim field mappings (from JavaScript-rendered page)
MYZMANIM_TO_ZMANIM = {
    "Alos Hashachar": "alot_hashachar",
    "Earliest Tallis": "misheyakir",
    "Sunrise": "netz_hachama",
    "Sunset": "shkia",
    "Chatzos": "chatzot_hayom",
    "Latest Shema GR\"A": "sof_zman_shema",
    "Latest Shacharis GR\"A": "sof_zman_tfilla",
    "Mincha Gedolah": "mincha_gedola",
    "Mincha Ketanah": "mincha_ketana",
    "Plag Hamincha": "plag_hamincha",
    "Tzais Hakochavim": "tset_hakohavim",
}

# Chabad.org field mappings (from JavaScript-rendered page)
CHABAD_TO_ZMANIM = {
    "Dawn (Alot Hashachar)": "alot_hashachar",
    "Earliest Tallit (Misheyakir)": "misheyakir",
    "Sunrise (Hanetz Hachama)": "netz_hachama",
    "Sunset (Shkiah)": "shkia",
    "Midday (Chatzot Hayom)": "chatzot_hayom",
    "Latest Shema": "sof_zman_shema",
    "Latest Shacharit": "sof_zman_tfilla",
    "Mincha Gedolah": "mincha_gedola",
    "Mincha Ketanah": "mincha_ketana",
    "Plag HaMincha": "plag_hamincha",
    "Nightfall (Tzeit Hakochavim)": "tset_hakohavim",
}

# Skyview API field mappings (Hebrew labels from JSON response)
SKYVIEW_TO_ZMANIM = {
    "עלות השחר א": "alot_hashachar",  # 90 minutes (stringent)
    "עלות השחר ב": "alot_hashachar_72",  # 72 minutes
    "טלית ותפילין": "misheyakir",
    "זריחה מישורית": "netz_hachama",
    "ק״ש גר״א": "sof_zman_shema",
    "תפילה גר״א": "sof_zman_tfilla",
    "ק״ש מג״א": "sof_zman_shema_mga",
    "תפילה מג״א": "sof_zman_tfilla_mga",
    "חצות": "chatzot_hayom",
    "מנחה גדולה": "mincha_gedola",
    "מנחה קטנה": "mincha_ketana",
    "פלג המנחה": "plag_hamincha",
    "שקיעה": "shkia",
    "הדלקת נרות": "candle_lighting",
    "מוצאי שבת": "tset_hakohavim",
    "מוצ״ש ר״ת": "tzait_rabbeinu_tam",
}


class FetchError(RuntimeError):
    """Raised when a remote fetch fails."""


def _fetch_hebcal(location: dict[str, Any], date_str: str) -> dict[str, str]:
    params = {
        "cfg": "json",
        "geo": "pos",
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "tzid": location["tzid"],
        "date": date_str,
    }
    url = f"{HEBCAL_BASE_URL}?{urlencode(params)}"
    try:
        with urlopen(url, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # pragma: no cover - network error surface
        raise FetchError(f"Failed to fetch {url}: {exc}") from exc

    times = payload.get("times", {})
    mapped: dict[str, str | None] = {}
    missing: list[str] = []
    for hebcal_key, local_key in HEBCAL_TO_ZMANIM.items():
        if hebcal_key not in times:
            missing.append(hebcal_key)
            continue
        mapped[local_key] = times.get(hebcal_key)

    if missing:
        raise FetchError(
            f"Missing keys from Hebcal response for {location['name']} {date_str}: "
            f"{', '.join(missing)}"
        )

    return mapped


def _fetch_myzmanim(location: dict[str, Any], date_str: str) -> dict[str, str]:
    """Fetch zmanim from MyZmanim.com using browser automation.
    
    MyZmanim renders its data via JavaScript, so we need playwright.
    
    LIMITATION: MyZmanim requires a paid account to access historical/future dates.
    This scraper only works for TODAY's date unless you have a subscription.
    
    URL pattern:
      https://www.myzmanim.com/search.aspx - search for location
      https://www.myzmanim.com/day.aspx?vars=XXX - daily view
      
    Returns:
        Dictionary mapping py-libhdate zman names to ISO time strings.
        
    Raises:
        FetchError: If playwright is not installed or scraping fails.
    """
    import re
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise FetchError(
            "MyZmanim scraping requires playwright. Install with:\n"
            "  pip install playwright && playwright install chromium"
        ) from exc
    
    # Check if requested date is today (MyZmanim free tier limitation)
    today = dt.date.today().isoformat()
    if date_str != today:
        raise FetchError(
            f"MyZmanim free tier only supports today's date ({today}). "
            f"Requested: {date_str}. A paid subscription is required for other dates."
        )
    
    # Field mapping from MyZmanim labels to our names
    myzmanim_labels = {
        "Talis": "misheyakir",
        "Sunrise": "netz_hachama",
        "Shema": "sof_zman_shema",
        "Shchrs": "sof_zman_tfilla",
        "Midday": "chatzot_hayom",
        "M.Gedola": "mincha_gedola",
        "M.Ketana": "mincha_ketana",
        "Plag": "plag_hamincha",
        "Sunset": "shkia",
        "Nightfall": "tset_hakohavim",
        "Candles": "candle_lighting",
    }
    
    mapped: dict[str, str | None] = {}
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Search for the location
        search_url = f"{MYZMANIM_BASE_URL}/search.aspx"
        page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
        
        # Fill search with location name
        page.fill("#txtSearch", location["name"])
        page.click("#btnSearch")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(2000)
        
        # Find and click the day.aspx link
        links = page.query_selector_all("a")
        day_link = None
        for link in links:
            href = link.get_attribute("href") or ""
            if "day.aspx" in href:
                day_link = href
                break
        
        if not day_link:
            browser.close()
            raise FetchError(f"MyZmanim: Could not find location '{location['name']}'")
        
        # Navigate to day page
        page.goto(f"{MYZMANIM_BASE_URL}/{day_link}", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(2000)
        
        # Extract zmanim from page text
        text = page.text_content("body")
        
        for line in text.split("\n"):
            line = line.strip()
            # Match patterns like "Sunrise 7:04"
            for label, local_key in myzmanim_labels.items():
                if line.startswith(label):
                    time_match = re.search(r"(\d{1,2}):(\d{2})", line)
                    if time_match:
                        hour, minute = int(time_match.group(1)), int(time_match.group(2))
                        # Assume PM for afternoon times
                        if label in ["Sunset", "Nightfall", "Candles"] and hour < 12:
                            hour += 12
                        elif label in ["M.Gedola", "M.Ketana", "Plag", "Midday"] and hour < 12:
                            hour += 12
                        iso_time = f"{date_str}T{hour:02d}:{minute:02d}:00"
                        mapped[local_key] = iso_time
                        break
        
        browser.close()
    
    if not mapped:
        raise FetchError(f"MyZmanim: No zmanim data found for {location['name']}")
    
    return mapped


def _fetch_chabad(location: dict[str, Any], date_str: str) -> dict[str, str]:
    """Fetch zmanim from Chabad.org.
    
    NOTE: Chabad.org has Cloudflare protection which blocks automated access.
    This function is currently non-functional due to bot protection.
    
    Possible workarounds:
    - Use a real browser with user interaction
    - Find an alternative API endpoint
    - Use a different data source
    
    Returns:
        Dictionary mapping py-libhdate zman names to ISO time strings.
        
    Raises:
        FetchError: Always - Cloudflare protection blocks automated access.
    """
    raise FetchError(
        "Chabad.org has Cloudflare bot protection which blocks automated scraping. "
        "This source is currently unavailable for automated data collection. "
        "Please use Hebcal or Skyview instead."
    )


def _fetch_skyview(location: dict[str, Any], date_str: str) -> dict[str, str]:
    """Fetch zmanim from Skyview/Chazon Shamayim REST API.
    
    Skyview (skyview2020.co.il) provides a REST API for Israeli locations
    with both Ashkenazi (Chazon Shamayim) and Sephardic calculation methods.
    
    API Endpoint:
      https://skyview2020.co.il/send-ajax.php
      
    Parameters:
      - LocName: Hebrew city name (e.g., ירושלים)
      - Region: "Israel" for Israeli cities
      - Method: "חזון_שמים" (Ashkenazi) or "ספרדי" (Sephardic)
      - year, month, day: Hebrew date
      
    Returns:
        Dictionary mapping py-libhdate zman names to ISO time strings.
        
    Raises:
        FetchError: If location not supported or API fails.
    """
    import re
    
    # Check if this is an Israeli location
    lat, lng = location["latitude"], location["longitude"]
    if not (29.0 <= lat <= 34.0 and 34.0 <= lng <= 36.0):
        raise FetchError(
            f"Skyview only supports Israeli locations. "
            f"{location['name']} ({lat}, {lng}) is outside Israel."
        )
    
    # Get Hebrew city name
    loc_name = location.get("name", "")
    hebrew_name = SKYVIEW_CITIES.get(loc_name)
    if not hebrew_name:
        # Try to use a custom hebrew_name field if provided
        hebrew_name = location.get("hebrew_name")
    if not hebrew_name:
        raise FetchError(
            f"Skyview: No Hebrew name mapping for '{loc_name}'. "
            f"Add it to SKYVIEW_CITIES or provide 'hebrew_name' in manifest."
        )
    
    # Convert Gregorian date to Hebrew date
    # We need to use py-libhdate's HebrewDate for this
    try:
        from hdate import HebrewDate
        from hdate.hebrew_date import Months
        date_obj = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
        hd = HebrewDate.from_gdate(date_obj)
        heb_year = hd.year
        heb_day = hd.day
        
        # Convert py-libhdate month to Skyview month numbering
        # py-libhdate: Tishrei=1, ..., Adar=6, Adar_I=7, Adar_II=8, Nisan=9...Elul=14
        # Skyview:     Tishrei=1, ..., Adar/Adar_I=6, Adar_II=7, Nisan=8...Elul=13
        pyl_month = hd.month.value
        if hd.is_leap_year:
            if hd.month == Months.ADAR_I:
                heb_month = 6  # Skyview Adar I
            elif hd.month == Months.ADAR_II:
                heb_month = 7  # Skyview Adar II
            elif pyl_month >= 9:  # Nisan onwards
                heb_month = pyl_month - 1  # Shift by 1
            else:
                heb_month = pyl_month  # Tishrei-Shevat unchanged
        else:
            # Non-leap year: py-libhdate uses Adar=6, skips 7,8, then Nisan=9
            # Skyview uses Adar=6, then Nisan=7
            if pyl_month == 6:  # Adar
                heb_month = 6
            elif pyl_month >= 9:  # Nisan onwards
                heb_month = pyl_month - 2  # Nisan=9->7, Iyyar=10->8, etc.
            else:
                heb_month = pyl_month  # Tishrei-Shevat unchanged
    except ImportError:
        raise FetchError(
            "Skyview requires hdate.HebrewDate for Hebrew date conversion. "
            "Make sure py-libhdate is installed."
        )
    
    # Build API URL
    params = {
        "LocName": hebrew_name,
        "Region": "Israel",
        "Method": "חזון_שמים",  # Ashkenazi method
        "year": heb_year,
        "month": heb_month,
        "day": heb_day,
    }
    url = f"{SKYVIEW_API_URL}?{urlencode(params)}"
    
    try:
        with urlopen(url, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise FetchError(f"Skyview API failed: {exc}") from exc
    
    # Parse the DailyZmanim array
    daily_zmanim = payload.get("DailyZmanim", [])
    if not daily_zmanim:
        raise FetchError(f"Skyview: No zmanim data in response for {loc_name}")
    
    mapped: dict[str, str | None] = {}
    
    for item in daily_zmanim:
        if not isinstance(item, list) or len(item) < 2:
            continue
        label, time_str = item[0], item[1]
        
        # Skip non-zmanim items (like Location, Date, etc.)
        if label in SKYVIEW_TO_ZMANIM:
            local_key = SKYVIEW_TO_ZMANIM[label]
            # Parse time (format: "HH:MM")
            time_match = re.match(r"(\d{1,2}):(\d{2})", time_str)
            if time_match:
                hour, minute = int(time_match.group(1)), int(time_match.group(2))
                iso_time = f"{date_str}T{hour:02d}:{minute:02d}:00"
                mapped[local_key] = iso_time
    
    if not mapped:
        raise FetchError(f"Skyview: Could not parse zmanim from response for {loc_name}")
    
    return mapped


def _load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "locations" not in data or "dates" not in data:
        raise ValueError("Manifest must include 'locations' and 'dates'")
    return data


# Registry of fetch functions by source name
FETCH_FUNCTIONS = {
    "hebcal": _fetch_hebcal,
    "myzmanim": _fetch_myzmanim,
    "chabad": _fetch_chabad,
    "skyview": _fetch_skyview,
}


def _build_reference(manifest: dict[str, Any], source: str = "hebcal") -> dict[str, Any]:
    """Build reference data from manifest using specified source.
    
    Args:
        manifest: The manifest containing locations and dates.
        source: The source to fetch from (hebcal, myzmanim, chabad, skyview).
        
    Returns:
        Reference dictionary with fetched zmanim data.
    """
    if source not in FETCH_FUNCTIONS:
        raise ValueError(f"Unknown source: {source}. Valid sources: {list(FETCH_FUNCTIONS.keys())}")
    
    fetch_fn = FETCH_FUNCTIONS[source]
    generated_at = dt.datetime.now(dt.timezone.utc).isoformat()
    reference: dict[str, Any] = {
        "source": f"{source}-zmanim",
        "generated_at": generated_at,
        "locations": [],
    }

    for location in manifest["locations"]:
        entry = {
            "name": location["name"],
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "tzid": location["tzid"],
            "tolerance_minutes": location.get("tolerance_minutes", 3),
            "dates": {},
        }
        for date_str in manifest["dates"]:
            try:
                entry["dates"][date_str] = fetch_fn(location, date_str)
            except FetchError as e:
                print(f"Warning: {e}", file=sys.stderr)
                entry["dates"][date_str] = {"_error": str(e)}
        reference["locations"].append(entry)

    return reference


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--source",
        choices=list(FETCH_FUNCTIONS.keys()),
        default="hebcal",
        help="Source to fetch zmanim from (default: hebcal)",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("tests/data/zmanim/manifest.json"),
        help="Path to manifest JSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path for reference JSON (default: based on source name)",
    )
    args = parser.parse_args()

    # Default output path based on source
    if args.output is None:
        args.output = Path(f"tests/data/zmanim/{args.source}_reference.json")

    manifest = _load_manifest(args.manifest)
    reference = _build_reference(manifest, source=args.source)
    args.output.write_text(json.dumps(reference, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
