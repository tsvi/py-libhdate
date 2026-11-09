# Executive Summary: API Design for Multi-Opinion Support
## Key Recommendations for py-libhdate

---

## Overview

This document summarizes the research and recommendations for implementing robust API design patterns in Python libraries that support multiple configurable options and halachic opinions (shitot).

---

## Key Findings from Research

### 1. Design Pattern Comparison

| Pattern | Use Case | Pros | Cons |
|---------|----------|------|------|
| **Strategy + Dataclass** | 3-10 strategies | Simple, type-safe | Limited flexibility |
| **Config + Enums** | Predefined options | Discoverable, validated | Enum explosion |
| **Plugin Registry** | User extensions | Highly extensible | Complex to implement |
| **Builder** | Complex configs | Fluent API, readable | Boilerplate |
| **Factory** | Preset configs | Clear intent, discoverable | Limited |

### 2. Best Practices Identified

1. **Configuration Objects > Magic Arguments**
   - Clearer intent: `ZmanimConfig(opinion="gra")` vs `Zmanim(..., opinion="gra")`
   - Easier to extend without changing function signatures
   - Better IDE support and documentation

2. **Dataclasses > Namedtuples**
   - Built-in validation via `__post_init__`
   - Easier mutation and composition
   - Better representation and equality
   - Easier to add defaults

3. **Enums > String Constants**
   - Type safety: compiler/IDE can catch typos
   - Discoverability: IDE can show available options
   - Forward compatibility: can add meaning without breaking code

4. **Validation at Construction Time**
   - Catch errors immediately
   - Clear error messages
   - Prevents cascading failures

5. **Cascading Defaults**
   - User override > Opinion defaults > Global defaults
   - Reduces parameter duplication
   - Maintains backward compatibility

6. **Support Multiple Configuration Sources**
   - File-based (JSON, YAML, TOML)
   - Environment variables
   - System defaults
   - User preferences
   - With clear precedence rules

---

## Recommended Architecture for py-libhdate

### Phase 1: Configuration Object (Implement First)

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional

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
    alot_hashachar_minutes: Optional[int] = None
    tzais_minutes: Optional[int] = None
    havdalah_minutes: Optional[int] = None
    candle_lighting_offset_minutes: int = 18
    
    @classmethod
    def for_opinion(cls, opinion: ZmanimOpinion) -> "ZmanimConfig":
        """Factory method for known opinions."""
        # Maps opinion to default values
        ...
    
    def get_tzais(self) -> int:
        """Get Tzais with cascading defaults."""
        # User override > Opinion default > Global default
        ...

# Update Zmanim to accept config
@dataclass
class Zmanim:
    date: dt.date
    location: Location
    config: ZmanimConfig = field(default_factory=ZmanimConfig)
    
    # Deprecated fields for backward compatibility
    candle_lighting_offset: int = 18
    
    def __post_init__(self):
        # Warn about deprecated parameters
        # Apply them to config for backward compatibility
        ...
```

**Benefits:**
- ✅ Zero breaking changes - old code still works
- ✅ Clear API for new code
- ✅ Type-safe with IDE support
- ✅ Easy to validate
- ✅ Foundation for future enhancements

### Phase 2: Factory Methods (Build on Phase 1)

```python
class ZmanimFactory:
    """Create pre-configured Zmanim instances."""
    
    @staticmethod
    def for_ashkenazi(date: dt.date, location: Location) -> Zmanim:
        return Zmanim(date, location, ZmanimConfig.for_opinion(ZmanimOpinion.GRA_ASHKENAZI))
    
    @staticmethod
    def for_sephardi(date: dt.date, location: Location) -> Zmanim:
        return Zmanim(date, location, ZmanimConfig.for_opinion(ZmanimOpinion.SEPHARDI))
    
    # ... more factory methods
```

**Benefits:**
- ✅ Discoverable through IDE autocompletion
- ✅ Clear, self-documenting code
- ✅ Easy to add more presets

### Phase 3: Plugin Support (Optional, for Advanced Users)

```python
class ZmanimOpinionRegistry:
    """Registry for custom opinions."""
    
    _opinions: Dict[str, Callable[[], ZmanimConfig]] = {}
    
    @classmethod
    def register(cls, name: str):
        """Decorator to register custom opinion."""
        def decorator(factory: Callable):
            cls._opinions[name] = factory
            return factory
        return decorator
```

**Benefits:**
- ✅ Users can add custom opinions without modifying library
- ✅ Third-party packages can register their own opinions
- ✅ Uses entry points for installed plugins

---

## Implementation Roadmap

### Release 1.2.0 (Phase 1 - Configuration)
**Target: 2-4 weeks**

- [ ] Create `ZmanimOpinion` enum
- [ ] Create `ZmanimConfig` dataclass with validation
- [ ] Update `Zmanim.__init__` to accept config
- [ ] Add deprecation warnings for old parameters
- [ ] Update docstrings
- [ ] Add comprehensive docstring examples
- [ ] Release documentation

**Breaking Changes:** None - fully backward compatible

### Release 1.3.0 (Phase 2 - Factories)
**Target: 4-6 weeks after 1.2**

- [ ] Implement `ZmanimFactory` class
- [ ] Add convenience factory methods
- [ ] Create builder pattern (optional)
- [ ] Update examples in docs
- [ ] Add more comprehensive tests

**Breaking Changes:** None - purely additive

### Release 2.0.0 (Phase 3 - Plugin System, Optional)
**Target: 6-12 months after 1.3**

- [ ] Implement `ZmanimOpinionRegistry`
- [ ] Add entry point support
- [ ] Plugin documentation
- [ ] Third-party plugin examples

**Breaking Changes:** Could remove deprecated parameters

---

## Key Recommendations by Use Case

### For Simple Usage
```python
# Just works with defaults
zmanim = Zmanim(date.today(), location)
```

### For Standard Opinions
```python
# Use factory methods - discoverable and clear
zmanim = ZmanimFactory.for_ashkenazi(date.today(), location)
zmanim = ZmanimFactory.stringent(date.today(), location)
```

### For Custom Values
```python
# Configuration objects - explicit and validated
config = ZmanimConfig(opinion=ZmanimOpinion.CUSTOM, tzais_minutes=50)
zmanim = Zmanim(date.today(), location, config)
```

### For Advanced Applications
```python
# Plugin registry - users can add their own
@ZmanimOpinionRegistry.register("my_community")
def my_community_config():
    return ZmanimConfig(...)

zmanim = Zmanim(date.today(), location, 
                ZmanimOpinionRegistry.get_opinion("my_community"))
```

---

## Important Design Decisions

### Decision 1: Configuration Object vs Keyword Arguments

**Chosen: Configuration Object (ZmanimConfig)**

**Rationale:**
- More explicit and self-documenting
- Easier to extend without breaking API
- Can be validated, serialized, composed
- Better type safety
- Common pattern in modern Python (Pydantic, dataclasses)

### Decision 2: Enum vs String Constants

**Chosen: Enum**

**Rationale:**
- Type safe - IDE catches typos
- Discoverable - IDE autocomplete shows options
- Can add metadata without breaking backward compat
- Easier to validate

### Decision 3: Deprecation vs Breaking Change

**Chosen: Deprecation (Backward Compatibility)**

**Rationale:**
- Respects existing users' code
- Smooth migration path
- Can warn users to update
- Remove old code in next major version

---

## Real-World Examples of Good Design

### Requests Library
```python
# Simple defaults
response = requests.get(url)

# Specific behaviors via objects
response = requests.get(url, auth=HTTPBasicAuth('u', 'p'))
response = requests.get(url, auth=HTTPDigestAuth('u', 'p'))

# Configuration via parameters
response = requests.get(url, verify=True)
response = requests.get(url, verify='/path/to/ca.crt')
```

### SQLAlchemy
```python
# Configuration via connection string
engine = create_engine('sqlite:///db.sqlite')
engine = create_engine('postgresql://user@localhost/db')

# Configuration via session options
session = Session(bind=engine, expire_on_commit=False)
```

### Pydantic
```python
# Configuration via ConfigDict
class Model(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    name: str
```

---

## Migration Strategy for Existing Users

### Phase 1 (Release 1.2) - Add New API
- Old code works unchanged
- Issue `DeprecationWarning` for old parameters
- New code can use `ZmanimConfig`
- Documentation shows both approaches

### Phase 2 (Release 1.3) - Encourage Migration
- Emphasis on new API in examples
- Migration guide in documentation
- More factory methods
- Still support old parameters

### Phase 3 (Release 2.0) - Optional Cleanup
- Can remove old parameter support
- Simplifies codebase
- Major version bump signals breaking change
- Users have 6-12 months notice

### Sample Deprecation Warning
```python
import warnings

warnings.warn(
    "candle_lighting_offset is deprecated. Use ZmanimConfig instead.\n"
    "Old: Zmanim(date, location, candle_lighting_offset=20)\n"
    "New: Zmanim(date, location, ZmanimConfig(candle_lighting_offset_minutes=20))",
    DeprecationWarning,
    stacklevel=2
)
```

---

## Documentation Structure

```
docs/
├── api/
│   ├── zmanim_config.md         # Configuration system
│   ├── zmanim_opinions.md       # Halachic opinions explained
│   └── zmanim_factory.md        # Factory methods
├── guides/
│   ├── migration_from_v1.md     # How to update old code
│   ├── custom_opinions.md       # How to define custom opinions
│   └── best_practices.md        # When to use what
├── examples/
│   ├── basic_usage.py           # Simple cases
│   ├── multiple_opinions.py     # Using different opinions
│   ├── custom_values.py         # Custom configuration
│   └── prayer_app.py            # Real-world app example
└── api_reference.md             # Full API docs
```

---

## Success Criteria

The implementation will be successful if:

1. **Backward Compatible** - Existing code continues to work without changes
2. **Type Safe** - IDE provides autocomplete and catches errors
3. **Discoverable** - Users can find options through IDE exploration
4. **Flexible** - Supports new opinions without API changes
5. **Well Documented** - Clear examples for all use cases
6. **Well Tested** - Comprehensive tests for all configurations
7. **Performant** - Minimal overhead for configuration

---

## Next Steps

1. **Review** - Share these recommendations with team
2. **Decide** - Choose which phases to implement
3. **Plan** - Create detailed implementation tasks
4. **Implement** - Start with Phase 1 (Configuration)
5. **Test** - Comprehensive testing of all scenarios
6. **Document** - Update docs and examples
7. **Release** - Follow semver (1.2.0, not 2.0.0 initially)
8. **Gather Feedback** - Get user feedback from early adopters

---

## Summary Table: Pattern Recommendations

| Aspect | Recommendation | Rationale |
|--------|---|---|
| **Config Storage** | Dataclass | Built-in validation, composition, serialization |
| **Predefined Options** | Enum | Type safety, discoverability |
| **API Surface** | Factory methods | Clear intent, discoverable |
| **Extension** | Registry pattern | Users can add without library changes |
| **Migration** | Deprecation warnings | Smooth transition for users |
| **Testing** | Parametrized tests | Cover all configuration combinations |
| **Documentation** | Multiple examples | Show simple and advanced usage |

---

## Conclusion

The recommended architecture provides:

✅ **Clarity** - Users know exactly what configuration they're using  
✅ **Flexibility** - Easy to add new opinions and options  
✅ **Backward Compatibility** - Existing code continues to work  
✅ **Type Safety** - IDE and type checkers can find errors  
✅ **Discoverability** - Options visible through IDE autocomplete  
✅ **Extensibility** - Users can add custom opinions  
✅ **Maintainability** - Clean separation of concerns  

This approach follows modern Python best practices and patterns used by successful libraries like Requests, SQLAlchemy, and Pydantic.
