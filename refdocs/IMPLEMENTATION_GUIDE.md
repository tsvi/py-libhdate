# Implementation Guide: Multi-Opinion Zmanim in py-libhdate
## Practical Examples and Migration Path

---

## Table of Contents
1. [Quick Start Examples](#quick-start-examples)
2. [Real-World Implementation Examples](#real-world-implementation-examples)
3. [Migration Guide for Existing Users](#migration-guide-for-existing-users)
4. [Advanced Use Cases](#advanced-use-cases)
5. [Testing Examples](#testing-examples)
6. [Documentation Examples](#documentation-examples)

---

## Quick Start Examples

### Example 1: Basic Usage (Backward Compatible)

```python
from hdate import Zmanim, Location
from datetime import date

# What works today (still works after update)
location = Location("New York")
zmanim = Zmanim(date.today(), location)

print(f"Tzais: {zmanim.tzais}")
print(f"Havdalah: {zmanim.havdalah}")
```

### Example 2: Using Predefined Opinions

```python
from hdate import Zmanim, Location, ZmanimConfig, ZmanimOpinion
from datetime import date

location = Location("New York")

# Use Ashkenazi GRA method (default)
config = ZmanimConfig(opinion=ZmanimOpinion.GRA_ASHKENAZI)
zmanim = Zmanim(date.today(), location, config)

# Use Magen Avraham method (more stringent)
config = ZmanimConfig(opinion=ZmanimOpinion.MAGEN_AVRAHAM)
zmanim = Zmanim(date.today(), location, config)

# Use Sephardi tradition
config = ZmanimConfig(opinion=ZmanimOpinion.SEPHARDI)
zmanim = Zmanim(date.today(), location, config)
```

### Example 3: Custom Values

```python
from hdate import Zmanim, Location, ZmanimConfig

location = Location("High Latitude City")

# Custom opinion with specific values
config = ZmanimConfig(
    opinion=ZmanimOpinion.CUSTOM,
    custom_params={
        "tzais_minutes": 50,
        "havdalah_minutes": 52,
        "alot_hashachar_minutes": 20,
    }
)
zmanim = Zmanim(date.today(), location, config)
```

### Example 4: Using Factory Methods

```python
from hdate import ZmanimFactory, Location
from datetime import date

location = Location("Tel Aviv")

# Factory methods for common use cases
zmanim = ZmanimFactory.for_ashkenazi(date.today(), location)
zmanim = ZmanimFactory.for_sephardi(date.today(), location)
zmanim = ZmanimFactory.for_chabad(date.today(), location)
zmanim = ZmanimFactory.stringent(date.today(), location)
```

### Example 5: Fluent Builder API

```python
from hdate import ZmanimBuilder, Location

location = Location("Jerusalem")

# Fluent, readable configuration
zmanim = (
    ZmanimBuilder()
    .for_date(date.today())
    .at_location(location)
    .with_opinion(ZmanimOpinion.MAGEN_AVRAHAM)
    .with_candle_lighting_offset(20)
    .build()
)

print(f"Candle lighting offset: {zmanim.config.candle_lighting_offset_minutes}")
```

---

## Real-World Implementation Examples

### Example 1: Prayer Service Application

```python
from hdate import Zmanim, Location, ZmanimConfig, ZmanimOpinion
from datetime import date, datetime, time, timedelta
from dataclasses import dataclass

@dataclass
class PrayerService:
    """Manages prayer times for a specific community."""
    
    location: Location
    opinion: ZmanimOpinion = ZmanimOpinion.GRA_ASHKENAZI
    languages: list[str] = None
    
    def __post_init__(self):
        if self.languages is None:
            self.languages = ["en", "he"]
    
    def get_prayer_times(self, service_date: date) -> dict:
        """Get prayer times for a specific date."""
        config = ZmanimConfig(opinion=self.opinion)
        zmanim = Zmanim(service_date, self.location, config)
        
        return {
            "shacharit_earliest": zmanim.alot_hashachar,
            "shacharit_latest": zmanim.sof_zman_tfilla,
            "mincha_earliest": zmanim.mincha_gedola,
            "mincha_latest": zmanim.plag_hamincha,
            "services_end": zmanim.tzais,
            "havdalah": zmanim.havdalah,
        }
    
    def get_services_for_week(self, start_date: date) -> dict[str, dict]:
        """Get prayer times for entire week."""
        services = {}
        for day_offset in range(7):
            current_date = start_date + timedelta(days=day_offset)
            day_name = current_date.strftime("%A")
            services[day_name] = self.get_prayer_times(current_date)
        return services
    
    def is_time_for_shacharit(self, now: datetime) -> bool:
        """Check if it's currently appropriate time for Shacharit."""
        zmanim = Zmanim(now.date(), self.location, ZmanimConfig(opinion=self.opinion))
        return zmanim.alot_hashachar <= now <= zmanim.sof_zman_tfilla
    
    def minutes_until_havdalah(self, now: datetime) -> int | None:
        """Get minutes until Havdalah."""
        zmanim = Zmanim(now.date(), self.location, ZmanimConfig(opinion=self.opinion))
        if now < zmanim.havdalah:
            return int((zmanim.havdalah - now).total_seconds() / 60)
        return None

# Usage
ny_community = PrayerService(
    location=Location("New York"),
    opinion=ZmanimOpinion.GRA_ASHKENAZI
)

today_times = ny_community.get_prayer_times(date.today())
print(f"Shacharit latest: {today_times['shacharit_latest']}")

week_times = ny_community.get_services_for_week(date.today())
```

### Example 2: Configuration-Based Zmanim Provider

```python
from hdate import Zmanim, Location, ZmanimConfig, ConfigurationManager
from pathlib import Path
from datetime import date
from functools import lru_cache

class ZmanimProvider:
    """Provides Zmanim with configuration management."""
    
    def __init__(self, config_path: Path = None):
        self.config_manager = ConfigurationManager()
        
        # Load in precedence order
        self.config_manager.load_from_system_defaults()
        self.config_manager.load_from_user_config()
        
        if config_path:
            self.config_manager.load_from_file(config_path)
        
        self.config_manager.load_from_env()
    
    @lru_cache(maxsize=128)
    def get_zmanim(self, date_str: str, location_str: str) -> dict:
        """Get Zmanim for date and location with caching."""
        date_obj = date.fromisoformat(date_str)
        location = Location(location_str)
        config = self.config_manager.get_config()
        
        zmanim = Zmanim(date_obj, location, config)
        
        return {
            "date": str(date_obj),
            "location": str(location),
            "alot_hashachar": zmanim.alot_hashachar.isoformat(),
            "tzais": zmanim.tzais.isoformat(),
            "havdalah": zmanim.havdalah.isoformat(),
            "opinion": config.opinion,
        }
    
    def refresh_cache(self):
        """Clear cache (useful if config changes)."""
        self.get_zmanim.cache_clear()

# Usage
provider = ZmanimProvider(Path("~/.hdate/config.json"))
times = provider.get_zmanim("2024-06-21", "New York")
```

### Example 3: REST API Service

```python
from flask import Flask, request, jsonify
from hdate import Zmanim, Location, ZmanimConfig, ZmanimOpinion
from datetime import date
from typing import Optional

app = Flask(__name__)

# Supported opinions
SUPPORTED_OPINIONS = {
    "gra": ZmanimOpinion.GRA_ASHKENAZI,
    "ma": ZmanimOpinion.MAGEN_AVRAHAM,
    "ashkenazi": ZmanimOpinion.GRA_ASHKENAZI,
    "sephardi": ZmanimOpinion.SEPHARDI,
    "chabad": ZmanimOpinion.CHABAD,
}

@app.route("/zmanim", methods=["GET"])
def get_zmanim():
    """
    Get Zmanim for a location.
    
    Query parameters:
    - location: Required. City name or coordinates (lat,lng)
    - date: Optional. YYYY-MM-DD format. Defaults to today.
    - opinion: Optional. One of: gra, ma, ashkenazi, sephardi, chabad
    """
    try:
        location_str = request.args.get("location")
        if not location_str:
            return {"error": "location parameter required"}, 400
        
        # Parse date
        date_str = request.args.get("date")
        if date_str:
            try:
                date_obj = date.fromisoformat(date_str)
            except ValueError:
                return {"error": "Invalid date format. Use YYYY-MM-DD"}, 400
        else:
            date_obj = date.today()
        
        # Parse opinion
        opinion_str = request.args.get("opinion", "gra").lower()
        if opinion_str not in SUPPORTED_OPINIONS:
            return {
                "error": f"Unknown opinion. Supported: {list(SUPPORTED_OPINIONS.keys())}"
            }, 400
        
        # Create Zmanim
        location = Location(location_str)
        config = ZmanimConfig(opinion=SUPPORTED_OPINIONS[opinion_str])
        zmanim = Zmanim(date_obj, location, config)
        
        return {
            "location": {
                "name": location.name,
                "latitude": location.latitude,
                "longitude": location.longitude,
            },
            "date": str(date_obj),
            "opinion": opinion_str,
            "zmanim": {
                "alot_hashachar": zmanim.alot_hashachar.isoformat(),
                "sof_zman_shema": zmanim.sof_zman_shema.isoformat(),
                "sof_zman_tfilla": zmanim.sof_zman_tfilla.isoformat(),
                "mincha_gedola": zmanim.mincha_gedola.isoformat(),
                "mincha_ketana": zmanim.mincha_ketana.isoformat(),
                "plag_hamincha": zmanim.plag_hamincha.isoformat(),
                "tzais": zmanim.tzais.isoformat(),
                "havdalah": zmanim.havdalah.isoformat(),
            },
        }
    
    except Exception as e:
        return {"error": str(e)}, 500

# Example requests:
# GET /zmanim?location=New%20York&opinion=gra
# GET /zmanim?location=Jerusalem&date=2024-06-21&opinion=ma
```

### Example 4: CLI Tool

```python
import click
from hdate import Zmanim, Location, ZmanimConfig, ZmanimOpinion
from datetime import date

@click.group()
def cli():
    """Zmanim calculator CLI."""
    pass

@cli.command()
@click.option("--location", required=True, help="City name or coordinates")
@click.option("--date", default=None, help="Date in YYYY-MM-DD format")
@click.option("--opinion", default="gra", 
              type=click.Choice(["gra", "ma", "sephardi", "chabad"]),
              help="Halachic opinion")
@click.option("--json", is_flag=True, help="Output as JSON")
def zmanim_cmd(location, date_str, opinion, json_output):
    """Get Zmanim for a location."""
    try:
        # Parse inputs
        location_obj = Location(location)
        date_obj = date.fromisoformat(date_str) if date_str else date.today()
        
        opinion_map = {
            "gra": ZmanimOpinion.GRA_ASHKENAZI,
            "ma": ZmanimOpinion.MAGEN_AVRAHAM,
            "sephardi": ZmanimOpinion.SEPHARDI,
            "chabad": ZmanimOpinion.CHABAD,
        }
        
        config = ZmanimConfig(opinion=opinion_map[opinion])
        zmanim = Zmanim(date_obj, location_obj, config)
        
        if json_output:
            import json
            output = {
                "location": location,
                "date": str(date_obj),
                "opinion": opinion,
                "alot_hashachar": zmanim.alot_hashachar.isoformat(),
                "tzais": zmanim.tzais.isoformat(),
                "havdalah": zmanim.havdalah.isoformat(),
            }
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo(f"Zmanim for {location} on {date_obj} ({opinion})")
            click.echo(f"Alot HaShachar: {zmanim.alot_hashachar.strftime('%H:%M')}")
            click.echo(f"Tzais: {zmanim.tzais.strftime('%H:%M')}")
            click.echo(f"Havdalah: {zmanim.havdalah.strftime('%H:%M')}")
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Exit(1)

if __name__ == "__main__":
    cli()

# Usage:
# python cli.py zmanim-cmd --location "New York" --opinion gra
# python cli.py zmanim-cmd --location Jerusalem --date 2024-06-21 --opinion ma --json
```

---

## Migration Guide for Existing Users

### For Users with Old Code

#### Old Way (Current)
```python
from hdate import Zmanim, Location

zmanim = Zmanim(date.today(), Location("New York"))
candle_lighting_time = zmanim.candle_lighting
```

#### New Way (Recommended, but old way still works)
```python
from hdate import Zmanim, Location, ZmanimConfig

zmanim = Zmanim(
    date.today(),
    Location("New York"),
    ZmanimConfig()  # Defaults to same behavior as before
)
candle_lighting_time = zmanim.candle_lighting
```

#### Deprecation Timeline

```
Version 1.2.0 (Current):
- New ZmanimConfig API available
- Old parameters still work with DeprecationWarning
- Documentation updated with migration guide

Version 1.3.0 (In 6 months):
- Old parameters issue DeprecationWarning
- New examples use ZmanimConfig

Version 2.0.0 (Breaking change):
- Old parameters removed
- ZmanimConfig required
- Major version bump
```

### Deprecation Warning Implementation

```python
import warnings

@dataclass
class Zmanim(TranslatorMixin):
    date: dt.date = field(default_factory=dt.date.today)
    location: Location = field(default_factory=Location)
    config: ZmanimConfig = field(default_factory=ZmanimConfig)
    
    # Deprecated fields
    candle_lighting_offset: int = 18
    havdalah_offset: int = 0
    
    def __post_init__(self) -> None:
        # Handle deprecated parameters
        if self.candle_lighting_offset != 18 or self.havdalah_offset != 0:
            warnings.warn(
                "candle_lighting_offset and havdalah_offset parameters are "
                "deprecated. Use ZmanimConfig instead.\n"
                "Example: ZmanimConfig(candle_lighting_offset_minutes=18)",
                DeprecationWarning,
                stacklevel=2
            )
            
            # Apply deprecated values to config
            if self.candle_lighting_offset != 18:
                self.config.candle_lighting_offset_minutes = self.candle_lighting_offset
            if self.havdalah_offset != 0:
                self.config.havdalah_offset_minutes = self.havdalah_offset
```

### Automated Migration Script

```python
"""
Script to help users migrate their code.
Usage: python migrate_zmanim_config.py --input old_script.py --output new_script.py
"""

import re
import sys
from pathlib import Path

def migrate_zmanim_code(content: str) -> str:
    """Migrate old Zmanim API to new config-based API."""
    
    # Pattern 1: Zmanim with candle_lighting_offset parameter
    pattern1 = re.compile(
        r'Zmanim\((.*?),\s*(.*?),\s*candle_lighting_offset\s*=\s*(\d+)(.*?)\)',
        re.DOTALL
    )
    
    def replace1(match):
        date_expr = match.group(1).strip()
        location_expr = match.group(2).strip()
        offset_value = match.group(3)
        other_params = match.group(4)
        
        return (
            f"Zmanim(\n"
            f"    {date_expr},\n"
            f"    {location_expr},\n"
            f"    ZmanimConfig(candle_lighting_offset_minutes={offset_value})\n"
            f"){other_params}"
        )
    
    content = pattern1.sub(replace1, content)
    
    # Ensure ZmanimConfig is imported
    if "ZmanimConfig" in content and "from hdate import" in content:
        content = re.sub(
            r'(from hdate import.*?Zmanim)',
            r'\1, ZmanimConfig',
            content
        )
    
    return content

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    content = input_path.read_text()
    migrated = migrate_zmanim_code(content)
    output_path.write_text(migrated)
    
    print(f"Migrated {input_path} -> {output_path}")
```

---

## Advanced Use Cases

### Multi-Community Support

```python
from hdate import ZmanimFactory, Location
from dataclasses import dataclass
from datetime import date

@dataclass
class CommunityConfig:
    """Configuration for different Jewish communities."""
    name: str
    locations: list[Location]
    opinion: str  # "gra", "ma", "sephardi", "chabad"
    language: str
    
    def get_zmanim(self, date_obj: date, location_index: int = 0):
        """Get Zmanim for this community."""
        location = self.locations[location_index]
        
        opinion_map = {
            "gra": ZmanimFactory.for_ashkenazi,
            "ma": ZmanimFactory.stringent,
            "sephardi": ZmanimFactory.for_sephardi,
            "chabad": ZmanimFactory.for_chabad,
        }
        
        factory = opinion_map.get(self.opinion, ZmanimFactory.for_ashkenazi)
        return factory(date_obj, location)

# Define communities
communities = {
    "ashkenazi_new_york": CommunityConfig(
        name="Ashkenazi - New York",
        locations=[Location("New York")],
        opinion="gra",
        language="en"
    ),
    "sephardi_jerusalem": CommunityConfig(
        name="Sephardi - Jerusalem",
        locations=[Location("Jerusalem")],
        opinion="sephardi",
        language="he"
    ),
    "chabad_brooklyn": CommunityConfig(
        name="Chabad - Brooklyn",
        locations=[Location("Brooklyn")],
        opinion="chabad",
        language="en"
    ),
}

# Usage
ny_community = communities["ashkenazi_new_york"]
zmanim = ny_community.get_zmanim(date.today())
```

### Dynamic Opinion Selection

```python
from hdate import Zmanim, Location, ZmanimConfig, ZmanimOpinion
from datetime import date
from enum import Enum

class UserPiety(Enum):
    """User's stringency level in observance."""
    LENIENT = "lenient"
    MODERATE = "moderate"
    STRINGENT = "stringent"

def get_recommended_opinion(user_piety: UserPiety) -> ZmanimOpinion:
    """Get recommended opinion based on user's stringency level."""
    
    piety_map = {
        UserPiety.LENIENT: ZmanimOpinion.SEPHARDI,  # Earlier Tzais
        UserPiety.MODERATE: ZmanimOpinion.GRA_ASHKENAZI,  # Middle ground
        UserPiety.STRINGENT: ZmanimOpinion.MAGEN_AVRAHAM,  # Later Tzais
    }
    
    return piety_map[user_piety]

class UserProfile:
    """User's Zmanim preferences."""
    
    def __init__(self, piety: UserPiety, custom_offset: int = None):
        self.piety = piety
        self.custom_offset = custom_offset
    
    def get_config(self) -> ZmanimConfig:
        """Get configuration based on user's profile."""
        opinion = get_recommended_opinion(self.piety)
        config = ZmanimConfig(opinion=opinion)
        
        if self.custom_offset:
            config.candle_lighting_offset_minutes = self.custom_offset
        
        return config
    
    def get_zmanim(self, date_obj: date, location: Location):
        """Get Zmanim for this user's preferences."""
        return Zmanim(date_obj, location, self.get_config())

# Usage
user = UserProfile(UserPiety.STRINGENT)
zmanim = user.get_zmanim(date.today(), Location("New York"))
```

---

## Testing Examples

### Unit Tests for Configuration

```python
import pytest
from datetime import date
from hdate import (
    Zmanim, Location, ZmanimConfig, ZmanimOpinion,
    ZmanimFactory, ConfigValidator
)

class TestZmanimConfig:
    """Test ZmanimConfig system."""
    
    def test_default_config(self):
        """Test default config uses GRA Ashkenazi."""
        config = ZmanimConfig()
        assert config.opinion == ZmanimOpinion.GRA_ASHKENAZI
        assert config.get_tzais() == 45
    
    @pytest.mark.parametrize("opinion,expected_tzais", [
        (ZmanimOpinion.GRA_ASHKENAZI, 45),
        (ZmanimOpinion.MAGEN_AVRAHAM, 72),
        (ZmanimOpinion.SEPHARDI, 19),
        (ZmanimOpinion.CHABAD, 45),
    ])
    def test_opinion_defaults(self, opinion, expected_tzais):
        """Test each opinion has correct Tzais default."""
        config = ZmanimConfig(opinion=opinion)
        assert config.get_tzais() == expected_tzais
    
    def test_custom_override(self):
        """Test custom values override opinion defaults."""
        config = ZmanimConfig(
            opinion=ZmanimOpinion.GRA_ASHKENAZI,
            tzais=50
        )
        assert config.get_tzais() == 50

class TestZmanimWithConfigs:
    """Test Zmanim calculations with different configs."""
    
    TEST_LOCATION = Location("New York")
    TEST_DATE = date(2024, 6, 21)
    
    def test_zmanim_with_gra_config(self):
        """Test Zmanim with GRA configuration."""
        config = ZmanimConfig(opinion=ZmanimOpinion.GRA_ASHKENAZI)
        zmanim = Zmanim(self.TEST_DATE, self.TEST_LOCATION, config)
        
        assert zmanim.tzais is not None
        assert zmanim.havdalah is not None
    
    def test_zmanim_with_magen_avraham_config(self):
        """Test Zmanim with Magen Avraham (more stringent)."""
        gra_config = ZmanimConfig(opinion=ZmanimOpinion.GRA_ASHKENAZI)
        ma_config = ZmanimConfig(opinion=ZmanimOpinion.MAGEN_AVRAHAM)
        
        gra_zmanim = Zmanim(self.TEST_DATE, self.TEST_LOCATION, gra_config)
        ma_zmanim = Zmanim(self.TEST_DATE, self.TEST_LOCATION, ma_config)
        
        # Magen Avraham should have later Tzais
        assert ma_zmanim.tzais > gra_zmanim.tzais

class TestZmanimFactory:
    """Test factory methods."""
    
    def test_factory_methods_exist(self):
        """Test that all factory methods work."""
        location = Location("New York")
        date_obj = date.today()
        
        assert ZmanimFactory.for_ashkenazi(date_obj, location) is not None
        assert ZmanimFactory.for_sephardi(date_obj, location) is not None
        assert ZmanimFactory.for_chabad(date_obj, location) is not None
        assert ZmanimFactory.stringent(date_obj, location) is not None

class TestConfigValidation:
    """Test configuration validation."""
    
    def test_valid_config_passes(self):
        """Test valid configuration passes validation."""
        config = ZmanimConfig(opinion=ZmanimOpinion.GRA_ASHKENAZI)
        validator = ConfigValidator()
        assert validator.validate_config(config)
    
    def test_invalid_opinion_fails(self):
        """Test invalid opinion fails validation."""
        config = ZmanimConfig(opinion="invalid_opinion")
        validator = ConfigValidator()
        assert not validator.validate_config(config)
    
    def test_negative_value_fails(self):
        """Test negative time values fail validation."""
        config = ZmanimConfig(tzais=-10)
        validator = ConfigValidator()
        assert not validator.validate_config(config)
```

### Integration Tests

```python
def test_zmanim_integration_multiple_opinions():
    """Integration test with multiple opinions and locations."""
    
    locations = [
        Location("New York"),
        Location("Jerusalem"),
        Location("London"),
    ]
    
    opinions = [
        ZmanimOpinion.GRA_ASHKENAZI,
        ZmanimOpinion.MAGEN_AVRAHAM,
        ZmanimOpinion.SEPHARDI,
    ]
    
    test_date = date(2024, 6, 21)
    
    results = {}
    
    for location in locations:
        for opinion in opinions:
            config = ZmanimConfig(opinion=opinion)
            zmanim = Zmanim(test_date, location, config)
            
            key = f"{location.name}_{opinion.value}"
            results[key] = {
                "alot_hashachar": zmanim.alot_hashachar,
                "tzais": zmanim.tzais,
                "havdalah": zmanim.havdalah,
            }
    
    # Verify all calculations completed
    assert len(results) == len(locations) * len(opinions)
    
    # Verify times are in correct order
    for result in results.values():
        assert result["alot_hashachar"] < result["tzais"]
        assert result["tzais"] < result["havdalah"]
```

---

## Documentation Examples

### README Update Example

```markdown
## Multiple Halachic Opinions (Shitot)

py-libhdate now supports multiple halachic opinions for Zmanim calculations:

### Quick Start

```python
from hdate import Zmanim, Location, ZmanimConfig, ZmanimOpinion
from datetime import date

location = Location("New York")

# Default (GRA Ashkenazi method)
zmanim = Zmanim(date.today(), location)

# Or specify an opinion
config = ZmanimConfig(opinion=ZmanimOpinion.MAGEN_AVRAHAM)
zmanim = Zmanim(date.today(), location, config)
```

### Supported Opinions

- **GRA_ASHKENAZI** - Vilna Gaon method (most common Ashkenazi)
- **MAGEN_AVRAHAM** - Stringent method
- **CHAZON_ISH** - Lithuanian yeshiva standard
- **SEPHARDI** - Traditional Sephardi method
- **CHABAD** - Chabad-Lubavitch tradition
- **CUSTOM** - Define your own parameters

### Using Factory Methods

```python
from hdate import ZmanimFactory

zmanim = ZmanimFactory.for_ashkenazi(date, location)
zmanim = ZmanimFactory.for_sephardi(date, location)
zmanim = ZmanimFactory.stringent(date, location)
```

### Custom Configuration

```python
config = ZmanimConfig(
    opinion=ZmanimOpinion.CUSTOM,
    custom_params={
        "tzais_minutes": 50,
        "havdalah_minutes": 52,
    }
)
zmanim = Zmanim(date, location, config)
```
```

---

## Summary

This implementation guide provides:

1. ✅ Quick start examples for common use cases
2. ✅ Real-world implementation patterns (prayer service, REST API, CLI)
3. ✅ Clear migration path for existing users
4. ✅ Advanced use cases (multi-community, dynamic selection)
5. ✅ Comprehensive testing strategies
6. ✅ Documentation examples

Users can adopt the new API at their own pace while old code continues to work with deprecation warnings.
