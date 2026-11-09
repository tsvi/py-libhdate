# Quick Reference Card: API Design for Multiple Options
## One-Page Cheat Sheet

---

## Recommended Architecture for py-libhdate

### Phase 1: Configuration Object (Implement First)
```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class ZmanimOpinion(str, Enum):
    GRA_ASHKENAZI = "gra_ashkenazi"
    MAGEN_AVRAHAM = "magen_avraham"
    CUSTOM = "custom"

@dataclass
class ZmanimConfig:
    opinion: ZmanimOpinion = ZmanimOpinion.GRA_ASHKENAZI
    tzais_minutes: Optional[int] = None
    havdalah_minutes: Optional[int] = None
    
    def __post_init__(self):
        # Validate configuration
        if self.tzais_minutes is not None and self.tzais_minutes < 0:
            raise ValueError("tzais_minutes must be non-negative")
```

### Phase 2: Factory Methods
```python
class ZmanimFactory:
    @staticmethod
    def for_ashkenazi(date, location):
        return Zmanim(date, location, ZmanimConfig())
    
    @staticmethod
    def for_sephardi(date, location):
        return Zmanim(date, location, 
                      ZmanimConfig(opinion=ZmanimOpinion.SEPHARDI))
```

### Phase 3: Plugin Registry (Advanced)
```python
class ZmanimOpinionRegistry:
    _registry = {}
    
    @classmethod
    def register(cls, name):
        def decorator(factory):
            cls._registry[name] = factory
            return factory
        return decorator
```

---

## Key Principles

| Principle | Why | How |
|-----------|-----|-----|
| **Explicit > Implicit** | Users understand what's happening | Use Config objects, not kwargs |
| **Type Safe** | Catch errors early | Use Enums, type hints, dataclasses |
| **Discoverable** | Users find options in IDE | Use Enums with autocomplete |
| **Backward Compatible** | Don't break existing code | Deprecation warnings, defaults |
| **Composable** | Easy to combine behaviors | Config objects, not inheritance |
| **Validatable** | Catch bad configs early | Validate in `__post_init__` |
| **Testable** | Easy to test scenarios | Parametrized tests with configs |

---

## Pattern Decision Tree

```
Choose Configuration Pattern:
  - Few fixed options? → Enum + dataclass
  - Many combinations? → Dataclass with validation
  - User-extensible? → Registry pattern
  - Complex building? → Builder pattern
  - Preset configs? → Factory pattern
  - All of above? → Layered approach
```

---

## Code Template: Configuration System

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional

# Step 1: Define enum for options
class MyOption(str, Enum):
    OPTION_A = "option_a"
    OPTION_B = "option_b"

# Step 2: Define config dataclass
@dataclass
class MyConfig:
    option: MyOption = MyOption.OPTION_A
    custom_value: Optional[int] = None
    
    def __post_init__(self):
        """Validate after initialization."""
        if self.custom_value is not None and self.custom_value < 0:
            raise ValueError("custom_value must be non-negative")
    
    @classmethod
    def for_option(cls, option: MyOption) -> "MyConfig":
        """Factory for each option."""
        defaults = {
            MyOption.OPTION_A: {"custom_value": 45},
            MyOption.OPTION_B: {"custom_value": 72},
        }
        return cls(option=option, **defaults.get(option, {}))

# Step 3: Use config in main class
@dataclass
class MyClass:
    config: MyConfig = field(default_factory=MyConfig)
    
    def get_value(self) -> int:
        return self.config.custom_value or 45

# Usage:
obj = MyClass()  # Defaults
obj = MyClass(config=MyConfig.for_option(MyOption.OPTION_B))
obj = MyClass(config=MyConfig(custom_value=50))
```

---

## Validation Checklist

```
Configuration Object Should Have:
☐ Type hints on all fields
☐ Default values or Optional typing
☐ Dataclass with validation in __post_init__
☐ Clear error messages for invalid configs
☐ Factory methods for common cases
☐ Immutable (frozen=True) optional
☐ Serializable (to JSON/YAML optional)
☐ Documented with examples

Main Class Should Have:
☐ Accept config as parameter
☐ Use config for behavior
☐ Cache config if needed
☐ Provide access to config
☐ Type hint the config type
```

---

## Testing Template

```python
import pytest

class TestConfig:
    @pytest.mark.parametrize("option,expected", [
        (MyOption.OPTION_A, 45),
        (MyOption.OPTION_B, 72),
    ])
    def test_options(self, option, expected):
        config = MyConfig.for_option(option)
        assert config.custom_value == expected
    
    def test_invalid_config_raises(self):
        with pytest.raises(ValueError):
            MyConfig(custom_value=-1)
    
    @pytest.mark.parametrize("config", [
        MyConfig(),
        MyConfig.for_option(MyOption.OPTION_A),
    ])
    def test_all_configs_work(self, config):
        obj = MyClass(config=config)
        assert obj.get_value() is not None
```

---

## Migration Path

```
Version 1.2.0 (Now):
  - New ZmanimConfig available
  - Old parameters work with DeprecationWarning
  - New examples use ZmanimConfig
  → Backward compatible ✓

Version 1.3.0 (In 3-6 months):
  - ZmanimConfig emphasized in docs
  - More factory methods added
  - Old parameters still work
  → Backward compatible ✓

Version 2.0.0 (6-12 months):
  - Can remove old parameter support
  - Major version signals breaking change
  → Breaking change, but users had warning ✓
```

---

## Deprecation Warning Example

```python
import warnings

def old_function(opinion_string):
    """Deprecated: use ZmanimConfig instead."""
    warnings.warn(
        "old_function is deprecated. "
        "Use: ZmanimConfig(opinion=ZmanimOpinion(opinion_string))",
        DeprecationWarning,
        stacklevel=2
    )
    return ZmanimConfig(opinion=ZmanimOpinion(opinion_string))
```

---

## Anti-Patterns to Avoid

```
❌ Deep inheritance hierarchies
✅ Composition with dataclasses

❌ String literals for options
✅ Use Enum for type safety

❌ Keyword argument overload
✅ Use config object

❌ Silent failures with bad config
✅ Validate in __post_init__

❌ Mutable default arguments
✅ Use field(default_factory=...)

❌ Undocumented magic parameters
✅ Make everything explicit

❌ Breaking changes without warning
✅ Use deprecation warnings
```

---

## Performance Tips

```python
# Precompute common configs
class PrecomputedConfigs:
    DEFAULT = ZmanimConfig()
    ASHKENAZI = ZmanimConfig.for_option(MyOption.OPTION_A)
    SEPHARDI = ZmanimConfig.for_option(MyOption.OPTION_B)

# Use for frequent access
config = PrecomputedConfigs.ASHKENAZI

# Cache computation results
from functools import cached_property

@dataclass
class MyClass:
    @cached_property
    def expensive_value(self) -> int:
        # Computed once, then cached
        return expensive_computation()
```

---

## Real-World Libraries Using These Patterns

| Library | Pattern | Example |
|---------|---------|---------|
| **Requests** | Strategy + Config | Auth objects, SSL verification |
| **SQLAlchemy** | Config objects | Connection strings, session options |
| **Pydantic** | Dataclass + Validation | ConfigDict, field validators |
| **FastAPI** | Enums + Type hints | Path parameters with choices |
| **Click** | Config objects | Command options and groups |

---

## Documentation Template

```markdown
## Configuration

### Simple Usage (Defaults)
\`\`\`python
zmanim = Zmanim(date, location)
\`\`\`

### Using Predefined Options
\`\`\`python
config = ZmanimConfig(opinion=ZmanimOpinion.MAGEN_AVRAHAM)
zmanim = Zmanim(date, location, config)
\`\`\`

### Using Factory Methods
\`\`\`python
zmanim = ZmanimFactory.stringent(date, location)
\`\`\`

### Custom Values
\`\`\`python
config = ZmanimConfig(opinion=ZmanimOpinion.CUSTOM, tzais_minutes=50)
zmanim = Zmanim(date, location, config)
\`\`\`

### Available Options
- GRA_ASHKENAZI (default): Most common Ashkenazi
- MAGEN_AVRAHAM: More stringent
- SEPHARDI: Sephardi tradition
- CUSTOM: Define your own
```

---

## Measurement: Did It Work?

Success means:
- ✅ Backward compatible (old code still works)
- ✅ Type safe (IDE catches errors)
- ✅ Discoverable (users find options in IDE)
- ✅ Flexible (easy to add new opinions)
- ✅ Tested (comprehensive test coverage)
- ✅ Documented (clear examples)
- ✅ Fast (minimal overhead)
- ✅ Maintainable (clear code structure)

---

## Resources

- **API_DESIGN_PATTERNS.md** - Comprehensive patterns (31KB)
- **CONFIGURATION_PATTERNS.md** - Config specifics (29KB)
- **IMPLEMENTATION_GUIDE.md** - Real examples (25KB)
- **CODE_PATTERNS_REFERENCE.md** - Quick patterns (16KB)
- **RECOMMENDATIONS_SUMMARY.md** - Executive summary (13KB)
- **DOCUMENTATION_INDEX.md** - Navigation guide (13KB)

Total: ~125KB of detailed patterns, examples, and guidance

---

## TL;DR

**What to implement:**
1. `ZmanimOpinion` enum
2. `ZmanimConfig` dataclass
3. Update `Zmanim` to use config
4. Add validation
5. Add factory methods
6. Deprecate old parameters

**Effort:** 2-4 weeks

**Risk:** Low (backward compatible)

**Impact:** High (enables multiple shitot support)

**Next Step:** Start with Phase 1, see `RECOMMENDATIONS_SUMMARY.md` for details
