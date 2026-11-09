# Advanced Configuration Patterns for Zmanim Implementation
## Architecture Guide for Multi-Opinion Support in Jewish Software

---

## Table of Contents
1. [Configuration Management Patterns](#configuration-management-patterns)
2. [Type-Safe Configuration with TypedDict](#type-safe-configuration-with-typeddict)
3. [Configuration File Support](#configuration-file-support)
4. [Dependency Injection Pattern](#dependency-injection-pattern)
5. [Composition Over Inheritance](#composition-over-inheritance)
6. [Validation Strategies](#validation-strategies)
7. [Performance Considerations](#performance-considerations)
8. [Testing Multiple Configurations](#testing-multiple-configurations)

---

## Configuration Management Patterns

### Pattern 1: Hierarchical Configuration with Defaults

Support multiple levels of defaults that cascade:

```python
from dataclasses import dataclass, field, asdict, replace
from typing import Any, Optional
import json
from pathlib import Path

@dataclass
class ZmanimDefaults:
    """Default values for different settings."""
    
    # Per-opinion defaults
    OPINION_DEFAULTS = {
        "gra_ashkenazi": {
            "alot_hashachar": 19,
            "tzais": 45,
            "havdalah": 50,
            "candle_lighting_offset": 18,
        },
        "magen_avraham": {
            "alot_hashachar": 72,
            "tzais": 72,
            "havdalah": 72,
            "candle_lighting_offset": 18,
        },
        "chazon_ish": {
            "alot_hashachar": 19,
            "tzais": 39,
            "havdalah": 42,
            "candle_lighting_offset": 18,
        },
        "sephardi": {
            "alot_hashachar": 19,
            "tzais": 19,
            "havdalah": 40,
            "candle_lighting_offset": 18,
        },
    }
    
    # Global defaults (most common case)
    GLOBAL_DEFAULTS = OPINION_DEFAULTS["gra_ashkenazi"]

@dataclass
class ZmanimConfig:
    """Hierarchical configuration with multiple fallback levels."""
    
    opinion: str = "gra_ashkenazi"
    alot_hashachar: Optional[int] = None  # User override
    tzais: Optional[int] = None  # User override
    havdalah: Optional[int] = None  # User override
    candle_lighting_offset: Optional[int] = None  # User override
    
    def get_alot_hashachar(self) -> int:
        """Get Alot HaShachar value with cascading defaults."""
        # 1. Explicit user value
        if self.alot_hashachar is not None:
            return self.alot_hashachar
        
        # 2. Opinion-specific default
        opinion_defaults = ZmanimDefaults.OPINION_DEFAULTS.get(self.opinion)
        if opinion_defaults and "alot_hashachar" in opinion_defaults:
            return opinion_defaults["alot_hashachar"]
        
        # 3. Global default
        return ZmanimDefaults.GLOBAL_DEFAULTS["alot_hashachar"]
    
    def get_tzais(self) -> int:
        """Get Tzais value with cascading defaults."""
        if self.tzais is not None:
            return self.tzais
        
        opinion_defaults = ZmanimDefaults.OPINION_DEFAULTS.get(self.opinion)
        if opinion_defaults and "tzais" in opinion_defaults:
            return opinion_defaults["tzais"]
        
        return ZmanimDefaults.GLOBAL_DEFAULTS["tzais"]
    
    def get_havdalah(self) -> int:
        """Get Havdalah value with cascading defaults."""
        if self.havdalah is not None:
            return self.havdalah
        
        opinion_defaults = ZmanimDefaults.OPINION_DEFAULTS.get(self.opinion)
        if opinion_defaults and "havdalah" in opinion_defaults:
            return opinion_defaults["havdalah"]
        
        return ZmanimDefaults.GLOBAL_DEFAULTS["havdalah"]
    
    # Convenience class methods
    @classmethod
    def for_opinion(cls, opinion: str) -> "ZmanimConfig":
        """Create a config for a specific opinion."""
        return cls(opinion=opinion)
    
    @classmethod
    def custom(cls, **overrides) -> "ZmanimConfig":
        """Create a custom config with specific overrides."""
        config = cls()
        for key, value in overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)
            else:
                raise ValueError(f"Unknown config key: {key}")
        return config
    
    def updated(self, **overrides) -> "ZmanimConfig":
        """Create a new config with some values overridden (immutable update)."""
        return replace(self, **overrides)

# Usage
config1 = ZmanimConfig()  # Defaults to GRA Ashkenazi
config2 = ZmanimConfig.for_opinion("magen_avraham")
config3 = ZmanimConfig.custom(opinion="chazon_ish", havdalah=50)
config4 = config1.updated(tzais=50)  # Override specific values

print(config1.get_tzais())  # 45 (GRA default)
print(config2.get_tzais())  # 72 (MA default)
print(config3.get_havdalah())  # 50 (custom)
```

### Pattern 2: Configuration Composition

Combine multiple configuration aspects:

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class OpinionConfig:
    """Base opinion configuration."""
    opinion_name: str
    alot_hashachar: int
    tzais: int
    havdalah: int

@dataclass
class LocationConfig:
    """Location-specific adjustments."""
    latitude: float
    elevation: Optional[int] = None
    use_degrees: bool = False  # For high latitudes

@dataclass
class UserPreferences:
    """User-specific preferences."""
    candle_lighting_offset: int = 18
    language: str = "en"
    include_all_zmanim: bool = True

@dataclass
class CompositeZmanimConfig:
    """Composite configuration combining all aspects."""
    opinion: OpinionConfig
    location: LocationConfig
    preferences: UserPreferences
    
    # Convenience properties
    @property
    def alot_hashachar(self) -> int:
        return self.opinion.alot_hashachar
    
    @property
    def tzais(self) -> int:
        return self.opinion.tzais
    
    @property
    def havdalah(self) -> int:
        return self.opinion.havdalah

# Usage
gra_opinion = OpinionConfig("gra_ashkenazi", 19, 45, 50)
ny_location = LocationConfig(latitude=40.7128, elevation=10)
user_prefs = UserPreferences(candle_lighting_offset=20, language="en")

config = CompositeZmanimConfig(gra_opinion, ny_location, user_prefs)
```

---

## Type-Safe Configuration with TypedDict

For configuration from external sources (JSON, YAML), use `TypedDict`:

```python
from typing import TypedDict, Literal, NotRequired
from typing_extensions import TypedDict  # For Python < 3.10

class OpinionDict(TypedDict):
    """Type-safe dictionary for opinion configuration."""
    name: str
    alot_hashachar: int
    tzais: int
    havdalah: int
    sof_zman_shema: Literal["gra_proportional", "ma_proportional"]
    sof_zman_tfilla: Literal["gra_proportional", "ma_proportional"]
    authority: NotRequired[str]
    year_introduced: NotRequired[int]

class LocationDict(TypedDict):
    """Type-safe dictionary for location."""
    latitude: float
    longitude: float
    elevation: NotRequired[int]
    timezone: str

class ZmanimConfigDict(TypedDict):
    """Top-level configuration dictionary."""
    opinion: OpinionDict
    location: LocationDict
    candle_lighting_offset: NotRequired[int]
    language: NotRequired[str]

# Loading from external source with type safety
def load_config_from_json(path: str) -> ZmanimConfigDict:
    """Load configuration from JSON with type checking."""
    with open(path) as f:
        data = json.load(f)
    
    # Validate structure
    config: ZmanimConfigDict = {
        "opinion": data["opinion"],
        "location": data["location"],
    }
    
    if "candle_lighting_offset" in data:
        config["candle_lighting_offset"] = data["candle_lighting_offset"]
    
    return config

# IDE will provide autocomplete and type checking
config_data: ZmanimConfigDict = {
    "opinion": {
        "name": "gra_ashkenazi",
        "alot_hashachar": 19,
        "tzais": 45,
        "havdalah": 50,
        "sof_zman_shema": "gra_proportional",
        "sof_zman_tfilla": "gra_proportional",
    },
    "location": {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "timezone": "America/New_York",
    },
    "candle_lighting_offset": 18,
}
```

---

## Configuration File Support

### JSON Configuration

```python
import json
from pathlib import Path
from dataclasses import asdict

# Save configuration
def save_config_json(config: ZmanimConfig, path: Path) -> None:
    """Save configuration to JSON file."""
    # Convert dataclass to dict, excluding None values
    data = {k: v for k, v in asdict(config).items() if v is not None}
    
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

# Load configuration
def load_config_json(path: Path) -> ZmanimConfig:
    """Load configuration from JSON file."""
    with open(path) as f:
        data = json.load(f)
    
    return ZmanimConfig(**data)

# Example JSON file
# {
#   "opinion": "gra_ashkenazi",
#   "tzais": 45,
#   "havdalah": 50,
#   "candle_lighting_offset": 18
# }
```

### YAML Configuration

```python
try:
    import yaml
except ImportError:
    yaml = None

def load_config_yaml(path: Path) -> ZmanimConfig:
    """Load configuration from YAML file."""
    if yaml is None:
        raise ImportError("PyYAML is required for YAML support")
    
    with open(path) as f:
        data = yaml.safe_load(f)
    
    return ZmanimConfig(**data)

# Example YAML file
# opinion: gra_ashkenazi
# tzais: 45
# havdalah: 50
# candle_lighting_offset: 18
```

### TOML Configuration (Python 3.11+)

```python
from tomllib import loads  # Python 3.11+

def load_config_toml(path: Path) -> ZmanimConfig:
    """Load configuration from TOML file."""
    with open(path, 'rb') as f:
        data = loads(f.read())
    
    return ZmanimConfig(**data['zmanim'])

# Example TOML
# [zmanim]
# opinion = "gra_ashkenazi"
# tzais = 45
# havdalah = 50
# candle_lighting_offset = 18
```

### Multi-Source Configuration with Precedence

```python
from typing import Optional
from pathlib import Path

class ConfigurationManager:
    """Manage configuration from multiple sources with precedence."""
    
    def __init__(self):
        self.config = ZmanimConfig()
    
    def load_from_system_defaults(self):
        """Load system-wide defaults (lowest priority)."""
        default_path = Path("/etc/hdate/zmanim.json")
        if default_path.exists():
            self.config = load_config_json(default_path)
    
    def load_from_user_config(self):
        """Load user configuration (medium priority)."""
        user_path = Path.home() / ".config" / "hdate" / "zmanim.json"
        if user_path.exists():
            loaded = load_config_json(user_path)
            self.config = self.config.updated(**asdict(loaded))
    
    def load_from_env(self):
        """Load from environment variables (high priority)."""
        import os
        
        env_mapping = {
            "HDATE_OPINION": "opinion",
            "HDATE_TZAIS": "tzais",
            "HDATE_HAVDALAH": "havdalah",
        }
        
        overrides = {}
        for env_var, config_key in env_mapping.items():
            if env_var in os.environ:
                value = os.environ[env_var]
                # Type conversion
                if config_key in ["tzais", "havdalah"]:
                    value = int(value)
                overrides[config_key] = value
        
        if overrides:
            self.config = self.config.updated(**overrides)
    
    def load_from_file(self, path: Path):
        """Load from specific file (highest priority)."""
        if path.suffix == '.json':
            loaded = load_config_json(path)
        elif path.suffix == '.yaml':
            loaded = load_config_yaml(path)
        elif path.suffix == '.toml':
            loaded = load_config_toml(path)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
        
        self.config = loaded
    
    def get_config(self) -> ZmanimConfig:
        """Get final configuration after all loads."""
        return self.config

# Usage with precedence (lowest to highest priority)
manager = ConfigurationManager()
manager.load_from_system_defaults()  # /etc/hdate/zmanim.json
manager.load_from_user_config()      # ~/.config/hdate/zmanim.json
manager.load_from_env()              # Environment variables
manager.load_from_file(Path("./local_config.json"))  # Local file

config = manager.get_config()
```

---

## Dependency Injection Pattern

Make configurations injectable for easier testing and flexibility:

```python
from abc import ABC, abstractmethod
from typing import Protocol

class ConfigProvider(Protocol):
    """Protocol for configuration providers."""
    
    def get_config(self) -> ZmanimConfig:
        """Get the current configuration."""
        ...

class DefaultConfigProvider:
    """Provides default configuration."""
    
    def __init__(self, opinion: str = "gra_ashkenazi"):
        self.opinion = opinion
    
    def get_config(self) -> ZmanimConfig:
        return ZmanimConfig.for_opinion(self.opinion)

class FileConfigProvider:
    """Provides configuration from file."""
    
    def __init__(self, path: Path):
        self.path = path
        self._config = load_config_json(path)
    
    def get_config(self) -> ZmanimConfig:
        return self._config

class EnvConfigProvider:
    """Provides configuration from environment."""
    
    def get_config(self) -> ZmanimConfig:
        manager = ConfigurationManager()
        manager.load_from_env()
        return manager.get_config()

# Zmanim class accepts injected provider
@dataclass
class Zmanim:
    date: dt.date
    location: Location
    config_provider: ConfigProvider = field(default_factory=DefaultConfigProvider)
    
    @property
    def config(self) -> ZmanimConfig:
        """Get config from provider."""
        return self.config_provider.get_config()
    
    @property
    def tzais(self) -> dt.datetime:
        config = self.config
        minutes = config.get_tzais()
        return self.sunset + dt.timedelta(minutes=minutes)

# Usage
# Default
zmanim = Zmanim(date, location)

# From file
config_provider = FileConfigProvider(Path("my_zmanim.json"))
zmanim = Zmanim(date, location, config_provider)

# From environment
env_provider = EnvConfigProvider()
zmanim = Zmanim(date, location, env_provider)

# For testing - can inject mock provider
class MockConfigProvider:
    def get_config(self) -> ZmanimConfig:
        return ZmanimConfig(opinion="test", tzais=50)

mock_zmanim = Zmanim(date, location, MockConfigProvider())
```

---

## Composition Over Inheritance

Instead of complex inheritance hierarchies, compose behaviors:

### Bad: Deep Inheritance

```python
# Anti-pattern - hard to maintain, inflexible
class ZmanimCalculator(ABC):
    pass

class TimeBasedZmanimCalculator(ZmanimCalculator):
    pass

class MinuteBasedZmanimCalculator(TimeBasedZmanimCalculator):
    pass

class GRAMinuteBasedZmanimCalculator(MinuteBasedZmanimCalculator):
    pass

# Ends up with deep, fragile hierarchy
```

### Good: Composition

```python
from abc import ABC, abstractmethod

class ZmanimCalculationMethod(ABC):
    """Strategy for calculating a single zman."""
    
    @abstractmethod
    def calculate(self, base_time: dt.datetime, location: Location) -> dt.datetime:
        pass

class MinuteOffsetMethod(ZmanimCalculationMethod):
    """Calculate based on minutes offset from base time."""
    
    def __init__(self, offset_minutes: int):
        self.offset_minutes = offset_minutes
    
    def calculate(self, base_time: dt.datetime, location: Location) -> dt.datetime:
        return base_time + dt.timedelta(minutes=self.offset_minutes)

class DegreeBasedMethod(ZmanimCalculationMethod):
    """Calculate based on solar degrees below horizon."""
    
    def __init__(self, degrees: float):
        self.degrees = degrees
    
    def calculate(self, base_time: dt.datetime, location: Location) -> dt.datetime:
        # Astronomical calculation
        raise NotImplementedError

class ProportionalMethod(ZmanimCalculationMethod):
    """Calculate based on proportion of day."""
    
    def __init__(self, proportion: float):
        self.proportion = proportion
    
    def calculate(self, base_time: dt.datetime, location: Location) -> dt.datetime:
        # Get sunrise/sunset times
        # Calculate proportion of day
        # Return calculated time
        raise NotImplementedError

# Compose these methods into a configuration
@dataclass
class ComposedZmanimConfig:
    """Configuration composed of individual calculation methods."""
    alot_hashachar_method: ZmanimCalculationMethod
    sof_zman_shema_method: ZmanimCalculationMethod
    tzais_method: ZmanimCalculationMethod
    havdalah_method: ZmanimCalculationMethod

# Create preset configurations by composition
GRA_CONFIG = ComposedZmanimConfig(
    alot_hashachar_method=MinuteOffsetMethod(-19),
    sof_zman_shema_method=ProportionalMethod(1/3),
    tzais_method=MinuteOffsetMethod(45),
    havdalah_method=MinuteOffsetMethod(50),
)

MAGEN_AVRAHAM_CONFIG = ComposedZmanimConfig(
    alot_hashachar_method=MinuteOffsetMethod(-72),
    sof_zman_shema_method=ProportionalMethod(1/3),
    tzais_method=MinuteOffsetMethod(72),
    havdalah_method=MinuteOffsetMethod(72),
)

# Much more flexible - can mix and match methods
CUSTOM_CONFIG = ComposedZmanimConfig(
    alot_hashachar_method=MinuteOffsetMethod(-20),
    sof_zman_shema_method=ProportionalMethod(1/3),
    tzais_method=DegreeBasedMethod(8.5),  # High latitude
    havdalah_method=MinuteOffsetMethod(50),
)

class ComposedZmanim:
    def __init__(self, date: dt.date, location: Location, config: ComposedZmanimConfig):
        self.date = date
        self.location = location
        self.config = config
    
    @property
    def alot_hashachar(self) -> dt.datetime:
        return self.config.alot_hashachar_method.calculate(self.sunrise, self.location)
    
    @property
    def tzais(self) -> dt.datetime:
        return self.config.tzais_method.calculate(self.sunset, self.location)
```

---

## Validation Strategies

### Comprehensive Validation

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class ValidationError:
    """Represents a validation error."""
    field: str
    message: str
    severity: str = "error"  # "error", "warning"

class ConfigValidator:
    """Validates Zmanim configuration."""
    
    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
    
    def validate_config(self, config: ZmanimConfig) -> bool:
        """Validate entire configuration. Returns True if valid."""
        self.errors.clear()
        self.warnings.clear()
        
        self._validate_opinion(config)
        self._validate_time_values(config)
        self._validate_logic(config)
        
        return len(self.errors) == 0
    
    def _validate_opinion(self, config: ZmanimConfig):
        """Validate opinion field."""
        valid_opinions = list(ZmanimDefaults.OPINION_DEFAULTS.keys())
        if config.opinion not in valid_opinions:
            self.errors.append(
                ValidationError(
                    "opinion",
                    f"Unknown opinion '{config.opinion}'. "
                    f"Valid options: {', '.join(valid_opinions)}"
                )
            )
    
    def _validate_time_values(self, config: ZmanimConfig):
        """Validate time values are in reasonable ranges."""
        for field_name in ["alot_hashachar", "tzais", "havdalah"]:
            value = getattr(config, field_name)
            if value is not None:
                if not isinstance(value, (int, float)):
                    self.errors.append(
                        ValidationError(
                            field_name,
                            f"Must be numeric, got {type(value).__name__}"
                        )
                    )
                elif value < 0:
                    self.errors.append(
                        ValidationError(
                            field_name,
                            f"Must be non-negative, got {value}"
                        )
                    )
                elif value > 120:
                    self.warnings.append(
                        ValidationError(
                            field_name,
                            f"Value {value} is unusually large",
                            severity="warning"
                        )
                    )
    
    def _validate_logic(self, config: ZmanimConfig):
        """Validate logical constraints."""
        alot = config.get_alot_hashachar()
        tzais = config.get_tzais()
        havdalah = config.get_havdalah()
        
        if tzais < 19:  # Tzais should be reasonable
            self.warnings.append(
                ValidationError(
                    "tzais",
                    f"Tzais value {tzais} is unusually small",
                    severity="warning"
                )
            )
        
        if havdalah > 90:  # Very stringent
            self.warnings.append(
                ValidationError(
                    "havdalah",
                    "Havdalah time is very late",
                    severity="warning"
                )
            )
    
    def get_error_messages(self) -> str:
        """Get formatted error messages."""
        lines = []
        for error in self.errors:
            lines.append(f"ERROR: {error.field}: {error.message}")
        for warning in self.warnings:
            lines.append(f"WARNING: {warning.field}: {warning.message}")
        return "\n".join(lines)

# Usage
validator = ConfigValidator()
config = ZmanimConfig(opinion="unknown_opinion")

if not validator.validate_config(config):
    print(validator.get_error_messages())
    raise ValueError("Invalid configuration")
```

---

## Performance Considerations

### Caching Configurations

```python
from functools import lru_cache
from typing import Tuple

class CachedConfigProvider:
    """Configuration provider with caching."""
    
    def __init__(self):
        self._cache = {}
    
    @staticmethod
    @lru_cache(maxsize=32)
    def _get_opinion_defaults(opinion: str) -> dict:
        """Cache opinion defaults lookup."""
        return ZmanimDefaults.OPINION_DEFAULTS.get(
            opinion,
            ZmanimDefaults.GLOBAL_DEFAULTS.copy()
        )
    
    def get_config(self, opinion: str) -> ZmanimConfig:
        """Get config with caching."""
        if opinion not in self._cache:
            defaults = self._get_opinion_defaults(opinion)
            self._cache[opinion] = ZmanimConfig(opinion=opinion, **defaults)
        return self._cache[opinion]

# Precompute common configurations
class PrecomputedConfigs:
    """Precomputed configurations for common use cases."""
    
    GRA_ASHKENAZI = ZmanimConfig.for_opinion("gra_ashkenazi")
    MAGEN_AVRAHAM = ZmanimConfig.for_opinion("magen_avraham")
    CHAZON_ISH = ZmanimConfig.for_opinion("chazon_ish")
    SEPHARDI = ZmanimConfig.for_opinion("sephardi")
    CHABAD = ZmanimConfig.for_opinion("chabad")

# Use precomputed
config = PrecomputedConfigs.GRA_ASHKENAZI
```

### Lazy Computation

```python
from functools import cached_property

@dataclass
class Zmanim:
    date: dt.date
    location: Location
    config: ZmanimConfig
    
    @cached_property
    def alot_hashachar(self) -> dt.datetime:
        """Lazily compute Alot HaShachar."""
        minutes = self.config.get_alot_hashachar()
        return self.sunrise - dt.timedelta(minutes=minutes)
    
    @cached_property
    def tzais(self) -> dt.datetime:
        """Lazily compute Tzais."""
        minutes = self.config.get_tzais()
        return self.sunset + dt.timedelta(minutes=minutes)
```

---

## Testing Multiple Configurations

### Parametrized Tests

```python
import pytest
from datetime import date, time

class TestZmanimConfig:
    """Test Zmanim configuration system."""
    
    @pytest.mark.parametrize("opinion,expected_tzais", [
        ("gra_ashkenazi", 45),
        ("magen_avraham", 72),
        ("chazon_ish", 39),
        ("sephardi", 19),
    ])
    def test_opinion_defaults(self, opinion, expected_tzais):
        """Test that each opinion has correct defaults."""
        config = ZmanimConfig.for_opinion(opinion)
        assert config.get_tzais() == expected_tzais
    
    @pytest.mark.parametrize("opinion", [
        "gra_ashkenazi", "magen_avraham", "chazon_ish", "sephardi"
    ])
    def test_config_is_valid(self, opinion):
        """Test that all predefined opinions are valid."""
        config = ZmanimConfig.for_opinion(opinion)
        validator = ConfigValidator()
        assert validator.validate_config(config)
    
    def test_custom_override_takes_precedence(self):
        """Test that custom values override opinion defaults."""
        config = ZmanimConfig(opinion="gra_ashkenazi", tzais=50)
        assert config.get_tzais() == 50  # Custom value
    
    def test_invalid_opinion_raises_error(self):
        """Test that invalid opinion raises error."""
        config = ZmanimConfig(opinion="invalid_opinion")
        validator = ConfigValidator()
        assert not validator.validate_config(config)
    
    def test_config_cascading_defaults(self):
        """Test the cascading default resolution."""
        # No custom value - uses opinion default
        config1 = ZmanimConfig(opinion="magen_avraham")
        assert config1.get_tzais() == 72
        
        # Custom value overrides opinion
        config2 = ZmanimConfig(opinion="magen_avraham", tzais=50)
        assert config2.get_tzais() == 50

class TestZmanimWithDifferentConfigs:
    """Test Zmanim calculations with different configurations."""
    
    TEST_DATE = date(2024, 6, 21)
    TEST_LOCATION = Location(latitude=40.7128, longitude=-74.0060)
    
    @pytest.mark.parametrize("config", [
        ZmanimConfig.for_opinion("gra_ashkenazi"),
        ZmanimConfig.for_opinion("magen_avraham"),
        ZmanimConfig.for_opinion("chazon_ish"),
    ])
    def test_zmanim_calculations_with_configs(self, config):
        """Test that Zmanim calculates correctly with each opinion."""
        zmanim = Zmanim(self.TEST_DATE, self.TEST_LOCATION, config)
        
        # All times should be datetime objects
        assert isinstance(zmanim.alot_hashachar, dt.datetime)
        assert isinstance(zmanim.tzais, dt.datetime)
        assert isinstance(zmanim.havdalah, dt.datetime)
        
        # Zmanim should be in correct order
        assert zmanim.alot_hashachar < zmanim.tzais
        assert zmanim.tzais < zmanim.havdalah

class TestConfigurationLoading:
    """Test loading configurations from files."""
    
    def test_load_json_config(self, tmp_path):
        """Test loading JSON configuration."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "opinion": "gra_ashkenazi",
            "tzais": 50,
        }))
        
        loaded = load_config_json(config_file)
        assert loaded.opinion == "gra_ashkenazi"
        assert loaded.tzais == 50
    
    def test_config_round_trip(self, tmp_path):
        """Test saving and loading configuration."""
        original = ZmanimConfig(opinion="magen_avraham", tzais=60)
        
        # Save
        save_path = tmp_path / "config.json"
        save_config_json(original, save_path)
        
        # Load
        loaded = load_config_json(save_path)
        
        # Verify
        assert loaded.opinion == original.opinion
        assert loaded.tzais == original.tzais
```

---

## Summary: Configuration Architecture Recommendation

For py-libhdate, implement this layered architecture:

```
┌─────────────────────────────────────────────┐
│         User-Facing API                     │
│  (Simple defaults, discoverable options)    │
└────────────┬────────────────────────────────┘
             │
┌────────────▼──────────────────────────────┐
│    Configuration Layer                     │
│    (ZmanimConfig, ZmanimOpinion)           │
│    (Defaults, validation, composition)     │
└────────────┬──────────────────────────────┘
             │
┌────────────▼──────────────────────────────┐
│    Calculation Layer                       │
│    (Actual time calculations)              │
│    (Pluggable calculation strategies)      │
└────────────┬──────────────────────────────┘
             │
┌────────────▼──────────────────────────────┐
│    Data Layer                              │
│    (Sunrise/sunset, astronomical data)     │
└──────────────────────────────────────────┘
```

This keeps concerns separated while allowing easy extension and customization at each level.
