# Code Patterns Reference: Multi-Configuration API Design
## Quick Reference for Common Patterns

---

## Table of Contents
1. [Configuration Patterns](#configuration-patterns)
2. [Validation Patterns](#validation-patterns)
3. [Factory Patterns](#factory-patterns)
4. [Plugin Patterns](#plugin-patterns)
5. [Testing Patterns](#testing-patterns)
6. [Migration Patterns](#migration-patterns)

---

## Configuration Patterns

### Pattern: Simple Configuration Object

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class Opinion(str, Enum):
    GRA = "gra"
    MA = "ma"

@dataclass
class Config:
    opinion: Opinion = Opinion.GRA
    custom_value: Optional[int] = None
    
    def get_value(self) -> int:
        """Get value with cascading defaults."""
        if self.custom_value is not None:
            return self.custom_value
        
        defaults = {"gra": 45, "ma": 72}
        return defaults.get(self.opinion.value, 45)
```

### Pattern: Configuration with Validation

```python
from dataclasses import dataclass
from typing import Any

@dataclass
class ValidatedConfig:
    opinion: Opinion = Opinion.GRA
    value: int = 45
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not isinstance(self.value, int):
            raise TypeError(f"value must be int, got {type(self.value)}")
        if self.value < 0:
            raise ValueError(f"value must be positive, got {self.value}")
        if self.value > 200:
            raise ValueError(f"value {self.value} is unreasonably large")
```

### Pattern: Configuration with Frozen State

```python
from dataclasses import dataclass

@dataclass(frozen=True)  # Immutable
class ImmutableConfig:
    """Immutable configuration - can be safely cached."""
    opinion: Opinion = Opinion.GRA
    value: int = 45
    
    def with_value(self, value: int) -> "ImmutableConfig":
        """Create new config with different value."""
        from dataclasses import replace
        return replace(self, value=value)

# Usage
config1 = ImmutableConfig()
config2 = config1.with_value(50)  # Creates new instance
```

### Pattern: Configuration with Metadata

```python
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class MetadataConfig:
    opinion: Opinion = Opinion.GRA
    value: int = 45
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def for_opinion(cls, opinion: Opinion) -> "MetadataConfig":
        """Create config with metadata about the opinion."""
        return cls(
            opinion=opinion,
            metadata={
                "authority": "Vilna Gaon" if opinion == Opinion.GRA else "Magen Avraham",
                "stringency": "moderate" if opinion == Opinion.GRA else "stringent",
            }
        )
```

---

## Validation Patterns

### Pattern: Single Field Validation

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    value: Optional[int] = None
    
    def __post_init__(self):
        if self.value is not None:
            self._validate_value()
    
    def _validate_value(self):
        """Validate value field."""
        if not isinstance(self.value, int):
            raise TypeError("value must be int")
        if self.value < 0 or self.value > 200:
            raise ValueError(f"value must be 0-200, got {self.value}")
```

### Pattern: Multi-Field Validation

```python
@dataclass
class MultiFieldConfig:
    start: int = 0
    end: int = 100
    
    def __post_init__(self):
        self._validate_start()
        self._validate_end()
        self._validate_relationship()
    
    def _validate_start(self):
        if self.start < 0:
            raise ValueError("start must be non-negative")
    
    def _validate_end(self):
        if self.end < 0:
            raise ValueError("end must be non-negative")
    
    def _validate_relationship(self):
        if self.start > self.end:
            raise ValueError("start must be <= end")
```

### Pattern: Conditional Validation

```python
from enum import Enum

class Mode(str, Enum):
    SIMPLE = "simple"
    ADVANCED = "advanced"

@dataclass
class ConditionalConfig:
    mode: Mode = Mode.SIMPLE
    custom_params: Optional[Dict] = None
    
    def __post_init__(self):
        if self.mode == Mode.ADVANCED and not self.custom_params:
            raise ValueError("ADVANCED mode requires custom_params")
        
        if self.mode == Mode.SIMPLE and self.custom_params:
            raise ValueError("SIMPLE mode doesn't accept custom_params")
```

### Pattern: Validation with Error Collection

```python
from dataclasses import dataclass
from typing import List

@dataclass
class ValidationError:
    field: str
    message: str

@dataclass
class ValidationConfig:
    value1: int = 0
    value2: int = 0
    
    def validate(self) -> List[ValidationError]:
        """Collect all validation errors."""
        errors = []
        
        if self.value1 < 0:
            errors.append(ValidationError("value1", "must be non-negative"))
        
        if self.value2 < 0:
            errors.append(ValidationError("value2", "must be non-negative"))
        
        if self.value1 > self.value2:
            errors.append(ValidationError("value1", "must be <= value2"))
        
        return errors
    
    def is_valid(self) -> bool:
        return len(self.validate()) == 0
```

---

## Factory Patterns

### Pattern: Static Factory Methods

```python
from dataclasses import dataclass

class Opinion(str, Enum):
    GRA = "gra"
    MA = "ma"

@dataclass
class Config:
    opinion: Opinion = Opinion.GRA
    value: int = 45
    
    @classmethod
    def for_gra(cls) -> "Config":
        return cls(opinion=Opinion.GRA, value=45)
    
    @classmethod
    def for_ma(cls) -> "Config":
        return cls(opinion=Opinion.MA, value=72)
    
    @classmethod
    def custom(cls, opinion: Opinion, value: int) -> "Config":
        return cls(opinion=opinion, value=value)

# Usage
config1 = Config.for_gra()
config2 = Config.for_ma()
config3 = Config.custom(Opinion.GRA, 50)
```

### Pattern: Factory Class

```python
class ConfigFactory:
    """Factory for creating configs."""
    
    _PRESETS = {
        "gra": Config(opinion=Opinion.GRA, value=45),
        "ma": Config(opinion=Opinion.MA, value=72),
    }
    
    @classmethod
    def create(cls, name: str) -> Config:
        """Create config by name."""
        if name not in cls._PRESETS:
            raise ValueError(f"Unknown preset: {name}")
        return cls._PRESETS[name]
    
    @classmethod
    def register(cls, name: str, config: Config) -> None:
        """Register custom preset."""
        cls._PRESETS[name] = config
    
    @classmethod
    def list_available(cls) -> list[str]:
        """List available presets."""
        return list(cls._PRESETS.keys())

# Usage
config = ConfigFactory.create("gra")
ConfigFactory.register("custom", Config(opinion=Opinion.GRA, value=50))
print(ConfigFactory.list_available())  # ['gra', 'ma', 'custom']
```

### Pattern: Builder Pattern

```python
@dataclass
class ConfigBuilder:
    """Build complex configurations."""
    
    opinion: Opinion = Opinion.GRA
    value: int = 45
    
    def with_opinion(self, opinion: Opinion) -> "ConfigBuilder":
        self.opinion = opinion
        return self
    
    def with_value(self, value: int) -> "ConfigBuilder":
        self.value = value
        return self
    
    def build(self) -> Config:
        return Config(opinion=self.opinion, value=self.value)

# Usage
config = (
    ConfigBuilder()
    .with_opinion(Opinion.MA)
    .with_value(72)
    .build()
)
```

---

## Plugin Patterns

### Pattern: Simple Registry

```python
from typing import Dict, Type, Callable

class ConfigRegistry:
    """Registry for custom configs."""
    
    _registry: Dict[str, Callable[[], Config]] = {}
    
    @classmethod
    def register(cls, name: str):
        """Decorator to register config factory."""
        def decorator(factory: Callable) -> Callable:
            cls._registry[name] = factory
            return factory
        return decorator
    
    @classmethod
    def get(cls, name: str) -> Config:
        """Get registered config."""
        if name not in cls._registry:
            raise ValueError(f"Unknown config: {name}")
        return cls._registry[name]()

# Usage
@ConfigRegistry.register("gra")
def gra_config() -> Config:
    return Config(opinion=Opinion.GRA, value=45)

config = ConfigRegistry.get("gra")
```

### Pattern: Plugin Discovery via Entry Points

```python
import importlib.metadata
from typing import Dict

class PluginRegistry:
    """Discover plugins via entry points."""
    
    _plugins: Dict[str, Config] = {}
    
    @classmethod
    def discover(cls, group: str = "my_app.configs"):
        """Discover and load plugins."""
        for entry_point in importlib.metadata.entry_points().get(group, []):
            try:
                factory = entry_point.load()
                config = factory()
                cls._plugins[entry_point.name] = config
            except Exception as e:
                print(f"Failed to load {entry_point.name}: {e}")
    
    @classmethod
    def get(cls, name: str) -> Config:
        """Get plugin config."""
        if name not in cls._plugins:
            raise ValueError(f"Unknown plugin: {name}")
        return cls._plugins[name]

# In pyproject.toml:
# [project.entry-points."my_app.configs"]
# gra = "myapp.plugins:gra_config"
```

---

## Testing Patterns

### Pattern: Parametrized Configuration Tests

```python
import pytest
from typing import List, Tuple

class TestConfigPatterns:
    """Test multiple configurations."""
    
    @pytest.mark.parametrize("opinion,value", [
        (Opinion.GRA, 45),
        (Opinion.MA, 72),
    ])
    def test_config_values(self, opinion: Opinion, value: int):
        """Test each configuration."""
        config = Config(opinion=opinion, value=value)
        assert config.value == value
    
    @pytest.mark.parametrize("config", [
        Config.for_gra(),
        Config.for_ma(),
    ])
    def test_config_is_valid(self, config: Config):
        """Test all configs are valid."""
        assert config.value > 0
```

### Pattern: Configuration Fixture

```python
import pytest

@pytest.fixture
def gra_config():
    """GRA configuration for testing."""
    return Config.for_gra()

@pytest.fixture
def ma_config():
    """Magen Avraham configuration for testing."""
    return Config.for_ma()

@pytest.fixture(params=["gra", "ma"])
def all_configs(request):
    """Parametrized fixture with all configs."""
    return ConfigFactory.create(request.param)

def test_with_config(all_configs):
    """Test with all configurations."""
    assert all_configs.value > 0
```

### Pattern: Snapshot Testing

```python
def test_config_snapshot(snapshot):
    """Test configuration against snapshot."""
    config = Config(opinion=Opinion.GRA, value=45)
    assert config == snapshot
```

---

## Migration Patterns

### Pattern: Deprecated Parameter

```python
import warnings
from typing import Optional

def create_zmanim(
    date,
    location,
    config: Optional[Config] = None,
    # Deprecated parameter
    opinion: Optional[str] = None,
):
    """Create Zmanim with optional config."""
    
    if opinion is not None:
        warnings.warn(
            "opinion parameter is deprecated. Use ZmanimConfig instead.",
            DeprecationWarning,
            stacklevel=2
        )
        if config is None:
            config = Config(opinion=Opinion(opinion))
    
    if config is None:
        config = Config()
    
    # ... rest of implementation
```

### Pattern: Version Check

```python
import sys

class LegacyAPI:
    """Backward compatible legacy API."""
    
    @staticmethod
    def old_function(opinion: str) -> Config:
        """Legacy function (deprecated)."""
        import warnings
        warnings.warn(
            "old_function is deprecated. Use ConfigFactory instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return ConfigFactory.create(opinion)
```

### Pattern: Adapter

```python
class ConfigAdapter:
    """Adapt old API to new API."""
    
    @staticmethod
    def from_old_style(opinion_str: str, **kwargs) -> Config:
        """Convert old-style parameters to Config."""
        return Config(
            opinion=Opinion(opinion_str),
            **kwargs
        )
```

---

## Common Pitfalls and How to Avoid Them

### Pitfall 1: Mutable Default Arguments

```python
# ❌ BAD
@dataclass
class BadConfig:
    items: list = []  # Shared across instances!

# ✅ GOOD
@dataclass
class GoodConfig:
    items: list = field(default_factory=list)  # New list per instance
```

### Pitfall 2: Missing Validation

```python
# ❌ BAD
@dataclass
class NoValidation:
    value: int = 0
    # No validation - can have invalid states

# ✅ GOOD
@dataclass
class WithValidation:
    value: int = 0
    
    def __post_init__(self):
        if self.value < 0:
            raise ValueError("value must be non-negative")
```

### Pitfall 3: Implicit Dependencies

```python
# ❌ BAD
@dataclass
class ImplicitConfig:
    tzais: int = 45
    # havdalah depends on tzais but isn't explicit
    
    @property
    def havdalah(self) -> int:
        return self.tzais + 5  # Hidden dependency!

# ✅ GOOD
@dataclass
class ExplicitConfig:
    tzais: int = 45
    havdalah: int = 50  # Explicit, not derived
    
    def __post_init__(self):
        # Optional: validate relationship
        if self.havdalah < self.tzais:
            raise ValueError("havdalah must be >= tzais")
```

### Pitfall 4: Breaking Changes Without Migration

```python
# ❌ BAD - Breaking change in 1.2.0
# Old API completely removed without warning

# ✅ GOOD - Deprecation path
# 1.2.0: New API available, old API issues DeprecationWarning
# 1.3.0: Old API still works, but warned prominently
# 2.0.0: Breaking change (major version)
```

### Pitfall 5: Enum Explosion

```python
# ❌ BAD - Too many enums
class TzaisMethod(Enum): ...
class HavdalahMethod(Enum): ...
class AlotMethod(Enum): ...
# Combinations explode: 3 × 3 × 3 = 27 possibilities

# ✅ GOOD - Use dataclass for flexibility
@dataclass
class Config:
    tzais_method: str = "minutes"
    tzais_value: int = 45
    havdalah_method: str = "minutes"
    havdalah_value: int = 50
```

---

## Performance Tips

### Pattern: Lazy Configuration

```python
from functools import cached_property

@dataclass
class LazyConfig:
    @cached_property
    def computed_value(self) -> int:
        """Computed only once, then cached."""
        # Expensive computation
        return sum(range(1000000))
```

### Pattern: Configuration Presets

```python
class PrecomputedConfigs:
    """Precomputed configs to avoid repeated initialization."""
    
    GRA = Config(opinion=Opinion.GRA, value=45)
    MA = Config(opinion=Opinion.MA, value=72)
    # Reuse instead of creating new instances
```

### Pattern: Configuration Caching

```python
from functools import lru_cache

@lru_cache(maxsize=32)
def get_config(opinion: str) -> Config:
    """Cache config creation."""
    return Config(opinion=Opinion(opinion))
```

---

## Summary: Pattern Decision Tree

```
Need configuration?
├── Simple (1-3 options)?
│   └── Use Enum + single field
├── Multiple related options?
│   └── Use Dataclass
├── Complex with dependencies?
│   └── Use Dataclass with validation
├── User-extensible?
│   ├── Small number of options?
│   │   └── Use Registry
│   └── Plugin system needed?
│       └── Use Entry Points + Registry
└── Complex construction?
    ├── Many required params?
    │   └── Use Builder
    └── Presets?
        └── Use Factory
```

---

## References

- Python Dataclasses: https://docs.python.org/3/library/dataclasses.html
- Enum: https://docs.python.org/3/library/enum.html
- Import Metadata: https://docs.python.org/3/library/importlib.metadata.html
- Design Patterns: https://refactoring.guru/design-patterns/python
- Pydantic (inspiration): https://pydantic-docs.helpmanual.io/
- SQLAlchemy (inspiration): https://docs.sqlalchemy.org/
