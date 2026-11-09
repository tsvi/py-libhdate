# API Design Patterns for Multi-Option Python Libraries
## Best Practices for Supporting Multiple Behaviors, Opinions, and Configurations

### Table of Contents
1. [Design Pattern Overview](#design-pattern-overview)
2. [Pattern 1: Strategy Pattern with Dataclasses](#pattern-1-strategy-pattern-with-dataclasses)
3. [Pattern 2: Configuration Objects and Enums](#pattern-2-configuration-objects-and-enums)
4. [Pattern 3: Plugin Architecture](#pattern-3-plugin-architecture)
5. [Pattern 4: Builder Pattern](#pattern-4-builder-pattern)
6. [Pattern 5: Factory Pattern](#pattern-5-factory-pattern)
7. [Backward Compatibility Strategies](#backward-compatibility-strategies)
8. [Real-World Examples](#real-world-examples)
9. [Recommendations for py-libhdate](#recommendations-for-py-libhdate)

---

## Design Pattern Overview

When designing APIs that support multiple configurable options, you need to balance:
- **Usability**: Easy for common cases, flexible for advanced cases
- **Extensibility**: Easy to add new behaviors without breaking existing code
- **Discoverability**: API should guide users to correct usage
- **Type Safety**: Leverage Python's type system for validation
- **Performance**: Minimal overhead for configuration lookup
- **Backward Compatibility**: Don't break existing users' code

### Core Design Principles

| Principle | Why It Matters |
|-----------|---|
| **Single Responsibility** | Each strategy/configuration handles one aspect |
| **Open/Closed** | Open for extension, closed for modification |
| **Dependency Inversion** | Depend on abstractions, not concrete implementations |
| **Explicit > Implicit** | Clear configuration beats magical defaults |
| **Fail Fast** | Validate configuration early with clear errors |

---

## Pattern 1: Strategy Pattern with Dataclasses

The **Strategy Pattern** is ideal for supporting multiple calculation methods or halachic opinions. Use dataclasses to define configuration that changes behavior.

### Basic Implementation

```python
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Protocol, Union
import datetime as dt

# Define the strategy interface
@dataclass
class ZmanimStrategy:
    """Base class for Zmanim calculation strategies (shitot)."""
    name: str
    description: str
    
    def calculate_alot_hashachar(self, sunrise: dt.datetime, location) -> dt.datetime:
        """Calculate Alot HaShachar (dawn) according to this shita."""
        raise NotImplementedError
    
    def calculate_tzais(self, sunset: dt.datetime, location) -> dt.datetime:
        """Calculate Tzais (nightfall) according to this shita."""
        raise NotImplementedError

# Concrete strategies
@dataclass
class GRAStrategy(ZmanimStrategy):
    """Vilna Gaon method - most common Ashkenazi approach."""
    alot_hashachar_minutes: int = 19
    tzais_minutes: int = 45
    havdalah_minutes: int = 50
    
    def calculate_alot_hashachar(self, sunrise: dt.datetime, location) -> dt.datetime:
        return sunrise - dt.timedelta(minutes=self.alot_hashachar_minutes)
    
    def calculate_tzais(self, sunset: dt.datetime, location) -> dt.datetime:
        return sunset + dt.timedelta(minutes=self.tzais_minutes)

@dataclass
class MagenAvrahamStrategy(ZmanimStrategy):
    """Magen Avraham method - stringent approach."""
    alot_hashachar_minutes: int = 72
    tzais_minutes: int = 72
    havdalah_minutes: int = 72
    
    def calculate_alot_hashachar(self, sunrise: dt.datetime, location) -> dt.datetime:
        return sunrise - dt.timedelta(minutes=self.alot_hashachar_minutes)
    
    def calculate_tzais(self, sunset: dt.datetime, location) -> dt.datetime:
        return sunset + dt.timedelta(minutes=self.tzais_minutes)

@dataclass
class DegreeBasedStrategy(ZmanimStrategy):
    """Degree-based calculations for high latitudes."""
    alot_hashachar_degrees: float = 16.1
    tzais_degrees: float = 8.5
    
    def calculate_alot_hashachar(self, sunrise: dt.datetime, location) -> dt.datetime:
        # Implementation would use astronomical calculations
        raise NotImplementedError("Requires astronomical library")

# Usage
class Zmanim:
    def __init__(self, date: dt.date, location, strategy: ZmanimStrategy = None):
        self.date = date
        self.location = location
        self.strategy = strategy or GRAStrategy(
            name="gra",
            description="Vilna Gaon method"
        )
    
    @property
    def alot_hashachar(self) -> dt.datetime:
        return self.strategy.calculate_alot_hashachar(self.sunrise, self.location)
    
    @property
    def tzais(self) -> dt.datetime:
        return self.strategy.calculate_tzais(self.sunset, self.location)
```

### Advantages
✅ Easy to add new strategies without modifying existing code  
✅ Clear separation of concerns  
✅ Type-safe with dataclasses  
✅ Can mix and match different strategies  

### Disadvantages
❌ Can become complex with many interdependent strategies  
❌ Strategy selection must be explicit  
❌ Hard to combine multiple strategies for same calculation  

---

## Pattern 2: Configuration Objects and Enums

Use **Enums** for predefined options and **Config Objects** for complex settings.

### Implementation with Enums

```python
from enum import Enum
from dataclasses import dataclass
from typing import Literal

class ZmanimOpinion(str, Enum):
    """Predefined halachic opinions for Zmanim calculations."""
    GRA_ASHKENAZI = "gra_ashkenazi"
    MAGEN_AVRAHAM = "magen_avraham"
    CHAZON_ISH = "chazon_ish"
    SEPHARDI_TRADITIONAL = "sephardi"
    CHABAD = "chabad"
    CUSTOM = "custom"

class TzaisMethod(str, Enum):
    """Different methods for calculating Tzais (nightfall)."""
    FIXED_19_MINUTES = "19_minutes"
    FIXED_39_MINUTES = "39_minutes"
    FIXED_45_MINUTES = "45_minutes"
    FIXED_72_MINUTES = "72_minutes"
    DEGREE_BASED_8_5 = "8_5_degrees"
    THREE_STARS = "three_stars"

@dataclass
class ZmanimConfig:
    """Configuration for Zmanim calculations."""
    opinion: ZmanimOpinion = ZmanimOpinion.GRA_ASHKENAZI
    tzais_method: TzaisMethod = TzaisMethod.FIXED_45_MINUTES
    candle_lighting_offset_minutes: int = 18
    high_latitude_method: Literal["degrees", "no_zmanim"] = "degrees"
    
    # Allow custom minute values for advanced users
    custom_alot_hashachar_minutes: int | None = None
    custom_tzais_minutes: int | None = None
    custom_havdalah_minutes: int | None = None

class Zmanim:
    def __init__(self, date: dt.date, location, config: ZmanimConfig | None = None):
        self.date = date
        self.location = location
        self.config = config or ZmanimConfig()
    
    @property
    def tzais(self) -> dt.datetime:
        """Calculate Tzais according to configured method."""
        tzais_map = {
            TzaisMethod.FIXED_19_MINUTES: self._calculate_tzais_19,
            TzaisMethod.FIXED_45_MINUTES: self._calculate_tzais_45,
            TzaisMethod.DEGREE_BASED_8_5: self._calculate_tzais_degrees,
        }
        
        calculator = tzais_map.get(
            self.config.tzais_method,
            self._calculate_tzais_45  # Default fallback
        )
        return calculator()
    
    def _calculate_tzais_19(self) -> dt.datetime:
        return self.sunset + dt.timedelta(minutes=19)
    
    def _calculate_tzais_45(self) -> dt.datetime:
        return self.sunset + dt.timedelta(minutes=45)
    
    def _calculate_tzais_degrees(self) -> dt.datetime:
        # Astronomical calculation for 8.5 degrees below horizon
        raise NotImplementedError()

# Usage examples
# Simple case - use defaults
zmanim_simple = Zmanim(dt.date.today(), location)

# Specific opinion
config = ZmanimConfig(opinion=ZmanimOpinion.MAGEN_AVRAHAM)
zmanim_stringent = Zmanim(dt.date.today(), location, config)

# Custom values
config_custom = ZmanimConfig(
    opinion=ZmanimOpinion.CUSTOM,
    custom_tzais_minutes=50
)
zmanim_custom = Zmanim(dt.date.today(), location, config_custom)
```

### Advantages
✅ Clear predefined options for users to discover  
✅ Type-safe with Enums  
✅ Easy to document and provide defaults  
✅ Scales well with many options  

### Disadvantages
❌ Enum combinations can grow exponentially  
❌ May need custom values beyond predefined options  

### Best Practice: Combine with Validation

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ZmanimConfig:
    opinion: ZmanimOpinion = ZmanimOpinion.GRA_ASHKENAZI
    custom_params: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.opinion == ZmanimOpinion.CUSTOM:
            required_params = {"tzais_minutes", "havdalah_minutes"}
            missing = required_params - set(self.custom_params.keys())
            if missing:
                raise ValueError(
                    f"Custom opinion requires these params: {missing}"
                )
        
        # Validate parameter ranges
        for key, value in self.custom_params.items():
            if not isinstance(value, (int, float)):
                raise TypeError(f"{key} must be numeric, got {type(value)}")
            if value < 0:
                raise ValueError(f"{key} must be non-negative, got {value}")
```

---

## Pattern 3: Plugin Architecture

For maximum extensibility, allow users to define and register their own strategies.

### Plugin Registry Pattern

```python
from abc import ABC, abstractmethod
from typing import Type, Dict, Callable

class ZmanimStrategyRegistry:
    """Registry for Zmanim calculation strategies."""
    
    _strategies: Dict[str, Type[ZmanimStrategy]] = {}
    
    @classmethod
    def register(cls, name: str):
        """Decorator to register a new strategy."""
        def decorator(strategy_class: Type[ZmanimStrategy]):
            if name in cls._strategies:
                raise ValueError(f"Strategy '{name}' already registered")
            cls._strategies[name] = strategy_class
            return strategy_class
        return decorator
    
    @classmethod
    def get_strategy(cls, name: str, **kwargs) -> ZmanimStrategy:
        """Get a strategy instance by name."""
        if name not in cls._strategies:
            available = ", ".join(cls._strategies.keys())
            raise ValueError(
                f"Unknown strategy '{name}'. Available: {available}"
            )
        return cls._strategies[name](**kwargs)
    
    @classmethod
    def list_available(cls) -> list[str]:
        """List all registered strategies."""
        return list(cls._strategies.keys())

# Register built-in strategies
@ZmanimStrategyRegistry.register("gra")
@dataclass
class GRAStrategy(ZmanimStrategy):
    name: str = "gra"
    description: str = "Vilna Gaon method"
    # ...

@ZmanimStrategyRegistry.register("magen_avraham")
@dataclass
class MagenAvrahamStrategy(ZmanimStrategy):
    name: str = "magen_avraham"
    description: str = "Magen Avraham method"
    # ...

# User can define custom strategy
@ZmanimStrategyRegistry.register("my_community")
@dataclass
class MyCommunityStrategy(ZmanimStrategy):
    """Custom strategy for my community."""
    name: str = "my_community"
    description: str = "Custom local practice"
    alot_hashachar_minutes: int = 20
    tzais_minutes: int = 48
    havdalah_minutes: int = 52
    
    def calculate_alot_hashachar(self, sunrise, location):
        return sunrise - dt.timedelta(minutes=self.alot_hashachar_minutes)
    
    def calculate_tzais(self, sunset, location):
        return sunset + dt.timedelta(minutes=self.tzais_minutes)

# Usage
class Zmanim:
    def __init__(self, date, location, strategy_name: str = "gra"):
        self.date = date
        self.location = location
        self.strategy = ZmanimStrategyRegistry.get_strategy(strategy_name)

# Discovery
available = ZmanimStrategyRegistry.list_available()
print(f"Available strategies: {available}")

zmanim = Zmanim(date, location, strategy_name="my_community")
```

### Entry Points Pattern (for installed plugins)

```toml
# pyproject.toml
[project.entry-points."hdate.zmanim_strategies"]
gra = "hdate.strategies:GRAStrategy"
magen_avraham = "hdate.strategies:MagenAvrahamStrategy"
my_plugin = "my_package.zmanim:CustomStrategy"
```

```python
# In your library
import importlib.metadata

def discover_strategies() -> dict[str, ZmanimStrategy]:
    """Discover all registered Zmanim strategies via entry points."""
    strategies = {}
    
    for entry_point in importlib.metadata.entry_points().get(
        "hdate.zmanim_strategies", []
    ):
        try:
            strategy_class = entry_point.load()
            strategies[entry_point.name] = strategy_class()
        except Exception as e:
            logger.warning(f"Failed to load strategy {entry_point.name}: {e}")
    
    return strategies
```

### Advantages
✅ Users can add custom strategies without modifying library code  
✅ Follows Open/Closed Principle perfectly  
✅ Supports installed plugins via entry points  
✅ Discovery mechanism for available options  

### Disadvantages
❌ More complex to implement  
❌ Requires clear documentation for custom strategy definition  
❌ Potential for bad implementations to break things  

---

## Pattern 4: Builder Pattern

For complex objects with many optional parameters.

```python
class ZmanimBuilder:
    """Builder for creating Zmanim objects with fluent API."""
    
    def __init__(self):
        self._date: dt.date | None = None
        self._location: Location | None = None
        self._config = ZmanimConfig()
    
    def for_date(self, date: dt.date) -> "ZmanimBuilder":
        """Set the date."""
        self._date = date
        return self
    
    def at_location(self, location: Location) -> "ZmanimBuilder":
        """Set the location."""
        self._location = location
        return self
    
    def with_opinion(self, opinion: ZmanimOpinion) -> "ZmanimBuilder":
        """Set the halachic opinion."""
        self._config.opinion = opinion
        return self
    
    def with_tzais_method(self, method: TzaisMethod) -> "ZmanimBuilder":
        """Set the Tzais calculation method."""
        self._config.tzais_method = method
        return self
    
    def with_custom_tzais(self, minutes: int) -> "ZmanimBuilder":
        """Set custom Tzais minutes."""
        self._config.opinion = ZmanimOpinion.CUSTOM
        self._config.custom_tzais_minutes = minutes
        return self
    
    def with_candle_lighting_offset(self, minutes: int) -> "ZmanimBuilder":
        """Set candle lighting offset."""
        self._config.candle_lighting_offset_minutes = minutes
        return self
    
    def build(self) -> Zmanim:
        """Build the Zmanim object."""
        if self._date is None:
            raise ValueError("Date must be set")
        if self._location is None:
            raise ValueError("Location must be set")
        
        return Zmanim(self._date, self._location, self._config)

# Usage - fluent and readable
zmanim = (
    ZmanimBuilder()
    .for_date(dt.date.today())
    .at_location(location)
    .with_opinion(ZmanimOpinion.MAGEN_AVRAHAM)
    .with_tzais_method(TzaisMethod.FIXED_72_MINUTES)
    .with_candle_lighting_offset(20)
    .build()
)
```

### Advantages
✅ Fluent, readable API  
✅ Validation happens at build time  
✅ Type-safe  
✅ Easy to add new options without breaking signature  

### Disadvantages
❌ More boilerplate code  
❌ Additional object allocation  

---

## Pattern 5: Factory Pattern

For creating pre-configured instances easily.

```python
class ZmanimFactory:
    """Factory for creating pre-configured Zmanim instances."""
    
    @staticmethod
    def for_ashkenazi(date: dt.date, location: Location) -> Zmanim:
        """Create Zmanim with Ashkenazi (GRA) preferences."""
        return Zmanim(
            date, 
            location,
            ZmanimConfig(opinion=ZmanimOpinion.GRA_ASHKENAZI)
        )
    
    @staticmethod
    def for_sephardi(date: dt.date, location: Location) -> Zmanim:
        """Create Zmanim with Sephardi preferences."""
        return Zmanim(
            date,
            location,
            ZmanimConfig(opinion=ZmanimOpinion.SEPHARDI_TRADITIONAL)
        )
    
    @staticmethod
    def for_chabad(date: dt.date, location: Location) -> Zmanim:
        """Create Zmanim with Chabad preferences."""
        return Zmanim(
            date,
            location,
            ZmanimConfig(
                opinion=ZmanimOpinion.CHABAD,
                tzais_method=TzaisMethod.FIXED_72_MINUTES
            )
        )
    
    @staticmethod
    def stringent(date: dt.date, location: Location) -> Zmanim:
        """Create Zmanim with stringent (Magen Avraham) times."""
        return Zmanim(
            date,
            location,
            ZmanimConfig(opinion=ZmanimOpinion.MAGEN_AVRAHAM)
        )
    
    @staticmethod
    def from_config_file(config_path: str, date: dt.date, location: Location) -> Zmanim:
        """Create Zmanim from a configuration file."""
        config = ZmanimConfig.from_file(config_path)
        return Zmanim(date, location, config)

# Usage
zmanim = ZmanimFactory.for_ashkenazi(dt.date.today(), location)
zmanim = ZmanimFactory.stringent(dt.date.today(), location)
```

### Advantages
✅ Discoverable through IDE autocompletion  
✅ Clear intent in code  
✅ Hides complexity  
✅ Easy to maintain presets  

---

## Backward Compatibility Strategies

When adding new configuration options:

### Strategy 1: Default Arguments

```python
# Old signature (still works)
def calculate_zmanim(date: dt.date, location: Location) -> dict:
    """Calculate default Zmanim."""
    config = ZmanimConfig()  # Uses defaults
    return _calculate_with_config(date, location, config)

# New signature (extended)
def calculate_zmanim(
    date: dt.date,
    location: Location,
    config: ZmanimConfig | None = None,
    **kwargs
) -> dict:
    """Calculate Zmanim with optional configuration."""
    if config is None:
        config = ZmanimConfig(**kwargs)  # Support old keyword args
    return _calculate_with_config(date, location, config)

# All these still work:
result = calculate_zmanim(date, location)  # Old way
result = calculate_zmanim(date, location, config)  # New way
result = calculate_zmanim(date, location, opinion="gra")  # Intermediate way
```

### Strategy 2: Deprecation Warnings

```python
import warnings

def get_zmanim_for_opinion(opinion_name: str, date: dt.date, location: Location):
    """Get Zmanim for an opinion (deprecated).
    
    Deprecated: Use Zmanim(date, location, ZmanimConfig(opinion=...)) instead.
    """
    warnings.warn(
        "get_zmanim_for_opinion is deprecated, use ZmanimConfig instead",
        DeprecationWarning,
        stacklevel=2
    )
    
    config = ZmanimConfig(opinion=ZmanimOpinion(opinion_name))
    return Zmanim(date, location, config)
```

### Strategy 3: Adapter Pattern

```python
class ZmanimAdapter:
    """Adapter to support old API while using new implementation."""
    
    @staticmethod
    def old_style_api(opinion: str, date: dt.date, location) -> dict:
        """Support old function-based API."""
        config = ZmanimConfig(opinion=ZmanimOpinion(opinion))
        zmanim = Zmanim(date, location, config)
        return {
            "alot_hashachar": zmanim.alot_hashachar,
            "tzais": zmanim.tzais,
            # ... other properties as dict
        }
```

### Strategy 4: Semantic Versioning

```
# Old code: uses version 1.0.0
from hdate import Zmanim
zmanim = Zmanim(date, location)  # Works with defaults

# Library updates to 1.1.0 (feature addition, backward compatible)
# Old code still works exactly the same

# Library updates to 2.0.0 (breaking change)
# Old code needs updates to explicit configuration
```

In `pyproject.toml`:
```toml
[project]
version = "1.2.0"  # MAJOR.MINOR.PATCH
```

### Strategy 5: Validation and Clear Error Messages

```python
class Zmanim:
    def __init__(self, date, location, config: ZmanimConfig | None = None, **kwargs):
        # Support both old and new ways
        if config is None and kwargs:
            # Warn about deprecated usage
            if "opinion" in kwargs or "tzais" in kwargs:
                warnings.warn(
                    "Passing opinion/tzais as kwargs is deprecated. "
                    "Use ZmanimConfig instead.",
                    DeprecationWarning,
                    stacklevel=2
                )
                config = ZmanimConfig(**kwargs)
            else:
                raise TypeError(f"Unexpected keyword arguments: {kwargs.keys()}")
        
        self.config = config or ZmanimConfig()
```

---

## Real-World Examples

### Example 1: Requests Library

The `requests` library supports multiple behaviors through:

```python
# Strategy via Auth objects
response = requests.get(url, auth=HTTPBasicAuth('user', 'pass'))
response = requests.get(url, auth=HTTPDigestAuth('user', 'pass'))

# Strategy via SSL verification
response = requests.get(url, verify=True)  # Default
response = requests.get(url, verify='/path/to/ca-bundle.crt')  # Custom

# Factory functions
session = requests.Session()
```

### Example 2: SQLAlchemy

Supports multiple database backends through configuration:

```python
# Different databases, same API
engine = create_engine('sqlite:///db.sqlite')
engine = create_engine('postgresql://user:password@localhost/db')
engine = create_engine('mysql+pymysql://user:password@localhost/db')

# Configuration objects
connection = engine.connect()
```

### Example 3: Pydantic Models

Uses configuration dataclasses:

```python
from pydantic import BaseModel, ConfigDict

class Model(BaseModel):
    model_config = ConfigDict(
        validate_assignment=True,
        str_strip_whitespace=True,
    )
    name: str
    age: int
```

### Example 4: Celery Tasks

Strategy pattern for task routing:

```python
@app.task
def process_data(data, routing_key='default'):
    """Process data with different strategies based on routing key."""
    strategies = {
        'fast': FastStrategy(),
        'thorough': ThoroughStrategy(),
        'gpu': GPUAcceleratedStrategy(),
    }
    strategy = strategies.get(routing_key, strategies['default'])
    return strategy.process(data)
```

---

## Recommendations for py-libhdate

Based on your existing codebase and ZMANIM_SHITOT_RESEARCH.md, here's a comprehensive recommendation:

### Recommended Architecture

#### Phase 1: Current State Enhancement

Your current code already uses some good patterns. Build on what works:

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal, Optional, Dict, Any

class ZmanimOpinion(str, Enum):
    """Predefined halachic opinions."""
    GRA_ASHKENAZI = "gra_ashkenazi"
    MAGEN_AVRAHAM = "magen_avraham"
    CHAZON_ISH = "chazon_ish"
    SEPHARDI = "sephardi"
    CHABAD = "chabad"
    CUSTOM = "custom"

@dataclass
class ZmanimConfig:
    """Configuration for Zmanim calculations."""
    
    opinion: ZmanimOpinion = ZmanimOpinion.GRA_ASHKENAZI
    
    # Opinion-specific parameters
    alot_hashachar_minutes: Optional[int] = None
    alot_hashachar_degrees: Optional[float] = None
    
    sof_zman_shema: Literal["gra_proportional", "ma_proportional", "fixed"] = "gra_proportional"
    sof_zman_tfilla: Literal["gra_proportional", "ma_proportional", "fixed"] = "gra_proportional"
    
    tzais_method: Literal["minutes", "degrees"] = "minutes"
    tzais_value: float = 45  # minutes if minutes method, degrees if degrees method
    
    havdalah_method: Literal["minutes", "degrees"] = "minutes"
    havdalah_value: float = 50
    
    candle_lighting_offset_minutes: int = 18
    high_latitude_method: Literal["degrees", "no_zmanim"] = "degrees"
    
    # For CUSTOM opinion, allow arbitrary parameters
    custom_params: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration."""
        if self.opinion == ZmanimOpinion.CUSTOM:
            if not self.custom_params:
                raise ValueError(
                    "CUSTOM opinion requires custom_params to be specified"
                )
        
        # Validate value ranges
        for attr in ["alot_hashachar_minutes", "tzais_value", "havdalah_value"]:
            value = getattr(self, attr)
            if value is not None and value < 0:
                raise ValueError(f"{attr} cannot be negative")
    
    @classmethod
    def for_opinion(cls, opinion: ZmanimOpinion) -> "ZmanimConfig":
        """Factory method for creating configs for known opinions."""
        opinion_defaults = {
            ZmanimOpinion.GRA_ASHKENAZI: {
                "alot_hashachar_minutes": 19,
                "tzais_value": 45,
                "havdalah_value": 50,
            },
            ZmanimOpinion.MAGEN_AVRAHAM: {
                "alot_hashachar_minutes": 72,
                "tzais_value": 72,
                "havdalah_value": 72,
            },
            ZmanimOpinion.CHAZON_ISH: {
                "alot_hashachar_minutes": 19,
                "tzais_value": 39,
                "havdalah_value": 42,
            },
            ZmanimOpinion.SEPHARDI: {
                "alot_hashachar_minutes": 19,
                "tzais_value": 19,
                "havdalah_value": 40,
            },
            ZmanimOpinion.CHABAD: {
                "alot_hashachar_minutes": 19,
                "tzais_value": 45,
                "havdalah_value": 72,
            },
        }
        
        if opinion not in opinion_defaults:
            raise ValueError(f"No preset available for {opinion}")
        
        return cls(opinion=opinion, **opinion_defaults[opinion])

# Update Zmanim class
@dataclass
class Zmanim(TranslatorMixin):
    date: dt.date = field(default_factory=dt.date.today)
    location: Location = field(default_factory=Location)
    config: ZmanimConfig = field(default_factory=ZmanimConfig)
    
    # For backward compatibility
    candle_lighting_offset: int = 18  # Deprecated, use config.candle_lighting_offset_minutes
    havdalah_offset: int = 0  # Deprecated
    
    def __post_init__(self) -> None:
        # Handle deprecated parameters
        if self.candle_lighting_offset != 18:
            warnings.warn(
                "candle_lighting_offset is deprecated, use ZmanimConfig instead",
                DeprecationWarning,
                stacklevel=2
            )
            self.config.candle_lighting_offset_minutes = self.candle_lighting_offset
        
        # ... existing validation code ...

# Usage examples
# Simple - uses defaults (GRA method, 45 minutes Tzais)
zmanim = Zmanim(dt.date.today(), location)

# Specific opinion
zmanim = Zmanim(dt.date.today(), location, 
                config=ZmanimConfig.for_opinion(ZmanimOpinion.MAGEN_AVRAHAM))

# Custom
config = ZmanimConfig(
    opinion=ZmanimOpinion.CUSTOM,
    custom_params={"tzais_minutes": 48, "havdalah_minutes": 52}
)
zmanim = Zmanim(dt.date.today(), location, config)
```

#### Phase 2: Plugin Support

```python
from typing import Type, Dict, Callable
import importlib.metadata

class ZmanimOpinionRegistry:
    """Registry for custom Zmanim opinions."""
    
    _opinions: Dict[str, Callable[[], ZmanimConfig]] = {}
    
    @classmethod
    def register(cls, name: str):
        """Decorator to register a custom opinion factory."""
        def decorator(factory_func: Callable[[], ZmanimConfig]):
            if name in cls._opinions:
                raise ValueError(f"Opinion '{name}' already registered")
            cls._opinions[name] = factory_func
            return factory_func
        return decorator
    
    @classmethod
    def get_opinion(cls, name: str) -> ZmanimConfig:
        """Get a registered opinion."""
        if name not in cls._opinions:
            available = ", ".join(cls._opinions.keys())
            raise ValueError(
                f"Unknown opinion '{name}'. Available: {available}"
            )
        return cls._opinions[name]()
    
    @classmethod
    def discover_from_entry_points(cls):
        """Discover opinions via entry points (for plugins)."""
        for entry_point in importlib.metadata.entry_points().get(
            "hdate.zmanim_opinions", []
        ):
            try:
                factory = entry_point.load()
                cls._opinions[entry_point.name] = factory
            except Exception as e:
                logger.warning(f"Failed to load opinion {entry_point.name}: {e}")

# Built-in registrations
@ZmanimOpinionRegistry.register("gra")
def _gra_opinion() -> ZmanimConfig:
    return ZmanimConfig.for_opinion(ZmanimOpinion.GRA_ASHKENAZI)

# User can register custom opinions
@ZmanimOpinionRegistry.register("my_community")
def _my_community_opinion() -> ZmanimConfig:
    return ZmanimConfig(
        opinion=ZmanimOpinion.CUSTOM,
        custom_params={"tzais_minutes": 50, "havdalah_minutes": 52}
    )
```

#### Phase 3: Migration Guide

For users currently using the API:

```python
# Old code (still works with deprecation warning)
zmanim = Zmanim(
    date,
    location,
    candle_lighting_offset=18,
    havdalah_offset=0
)

# New recommended code
config = ZmanimConfig(
    opinion=ZmanimOpinion.GRA_ASHKENAZI,
    candle_lighting_offset_minutes=18
)
zmanim = Zmanim(date, location, config)

# Or using convenience factory
zmanim = Zmanim(
    date,
    location,
    config=ZmanimConfig.for_opinion(ZmanimOpinion.GRA_ASHKENAZI)
)
```

### Implementation Checklist for py-libhdate

- [ ] Create `ZmanimOpinion` enum with all major opinions
- [ ] Create `ZmanimConfig` dataclass with validation
- [ ] Add factory methods to `ZmanimConfig` for known opinions
- [ ] Update `Zmanim.__init__` to accept `ZmanimConfig`
- [ ] Update calculation methods to use config values
- [ ] Add deprecation warnings for old parameters
- [ ] Create `ZmanimOpinionRegistry` for extensibility
- [ ] Document the new API with migration guide
- [ ] Add type hints throughout
- [ ] Create tests for different opinions
- [ ] Update README with new usage examples
- [ ] Consider entry points for plugin support

### Documentation Structure

```
docs/
├── api/
│   ├── configuration.md      # ZmanimConfig and ZmanimOpinion
│   ├── opinions.md           # Explanation of each opinion
│   └── custom_opinions.md    # How to create custom opinions
├── guides/
│   ├── migration_guide.md    # From old to new API
│   └── best_practices.md     # When to use which opinion
└── examples/
    ├── basic_usage.py
    ├── custom_opinion.py
    └── high_latitude.py
```

---

## Summary Table: When to Use Each Pattern

| Pattern | Best For | Complexity | Extensibility |
|---------|----------|-----------|---|
| **Strategy with Dataclass** | Small number of strategies | Low | Medium |
| **Config + Enums** | Predefined options only | Low | Low |
| **Plugin Registry** | User-defined extensions | High | Very High |
| **Builder** | Complex configurations | Medium | Medium |
| **Factory** | Preset configurations | Low | Medium |

**Recommendation for py-libhdate**: Start with **Config + Enums** (Phase 1), add **Factory methods** (Phase 2), and support **Plugin Registry** for advanced users (Phase 3).

This provides a smooth progression from simple to advanced, with each layer building on the previous one.
