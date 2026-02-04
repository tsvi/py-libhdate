"""
Configuration for Zmanim calculations supporting multiple halachic opinions.

This module provides a flexible configuration system for calculating Jewish
prayer times (zmanim) according to different rabbinic authorities and customs.
Users can select from predefined calculation methods or provide custom values.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CalculationMethod(Enum):
    """
    Halachic calculation methods for determining zmanim.

    GRA (Vilna Gaon) / Baal HaTanya:
        - Dawn (alot): 16.1 degrees below horizon (or other values)
        - Sunrise to sunset defines the "day"
        - Shema time: 1/3 of day from sunrise
        - Tfilla time: 1/3 of day from sunrise
        - Mincha times: based on shaot zmaniyot from sunrise

    MGA (Magen Avraham):
        - Dawn (alot): 72 minutes before sunrise (or other values)
        - Dawn to nightfall defines the "light period"
        - Shema time: 1/3 of light hours from dawn
        - Tfilla time: 1/3 of light hours from dawn
        - Mincha times: based on shaot zmaniyot from dawn

    Note: GRA and Baal HaTanya use the same calculation method (sunrise-to-sunset).
    BAAL_HATANYA is provided as an alias for GRA for clarity.
    """

    GRA = "gra"
    """Vilna Gaon - calculates from sunrise to sunset."""

    BAAL_HATANYA = "gra"
    """Baal HaTanya (Alter Rebbe) - uses same calculation as GRA.

    Alias for GRA (sunrise to sunset).
    """

    MGA = "mga"
    """Magen Avraham - calculates from dawn to nightfall."""


class ZmanType(Enum):
    """
    Types of zmanim that can be calculated.

    Each zman type specifies:
    - The configuration field to use from ZmanimConfig
    - The default zenith angle if not configured
    - Whether it's a rising (sunrise-like) or setting (sunset-like) time
    """

    NETZ_HACHAMA = "netz_hachama"  # Sunrise
    SHKIA = "shkia"  # Sunset
    ALOT_HASHACHAR = "alot_hashachar"  # Dawn
    MISHEYAKIR = "misheyakir"  # When light enough to recognize a friend
    CHATZOT = "chatzot"  # Midday
    TZAIT_HAKOCHAVIM = "tzait_hakochavim"  # Nightfall (regular)
    TZAIT_FAST_DAY = "tzait_fast_day"  # Nightfall (fast day)
    TZAIT_SHABBAT = "tzait_shabbat"  # Nightfall (Shabbat/Yom Tov)


@dataclass(frozen=True)
class ZmanMethod:
    """
    Represents a calculation method for a specific zman.

    A zman can be calculated using either:
    - Degrees below/above the horizon (astronomical calculation)
    - Fixed minutes offset from sunrise/sunset

    Examples:
        >>> # Alot HaShachar at 16.1 degrees (GRA standard)
        >>> alot = ZmanMethod(degrees=16.1)

        >>> # Tzait HaKochavim at 72 minutes after sunset (Magen Avraham)
        >>> tzait = ZmanMethod(minutes=72)

        >>> # Custom degree calculation
        >>> custom = ZmanMethod(degrees=18.5)
    """

    degrees: float | None = None
    minutes: float | None = None

    def __post_init__(self) -> None:
        """Validate that exactly one calculation method is specified."""
        if self.degrees is None and self.minutes is None:
            raise ValueError("Either degrees or minutes must be specified")
        if self.degrees is not None and self.minutes is not None:
            raise ValueError("Cannot specify both degrees and minutes")
        if self.degrees is not None and self.degrees < 0:
            raise ValueError("Degrees must be non-negative")
        if self.minutes is not None and self.minutes < 0:
            raise ValueError("Minutes must be non-negative")

    def __call__(
        self,
        is_rising: bool,
        get_sun_time: Callable[[float, bool], int],
    ) -> int:
        """
        Calculate the zman time using this method.

        Args:
            is_rising: True for sunrise-like times, False for sunset-like times
            get_sun_time: Callable(zenith, is_rising) -> time_in_minutes for
                degree-based calculations

        Returns:
            Time in minutes from midnight UTC
        """
        # Handle degree-based calculations
        if self.degrees is not None:
            zenith = 90.0 + self.degrees
            return get_sun_time(zenith, is_rising)

        # Handle minutes-based calculations
        assert self.minutes is not None
        if is_rising:
            base_sunrise = get_sun_time(ZmanDefaults.NETZ_SHKIA_ZENITH, True)
            return int(base_sunrise - self.minutes)
        base_sunset = get_sun_time(ZmanDefaults.NETZ_SHKIA_ZENITH, False)
        return int(base_sunset + self.minutes)


@dataclass(frozen=True)
class ZmanCalculation:
    """
    Request object for calculating a single zman time.

    Encapsulates all parameters needed to calculate a zman's time,
    replacing the previous multi-parameter approach.

    Attributes:
        method: ZmanMethod to use (always set, never None)
        default_zenith: Default zenith angle (for reference/fallback)
        is_rising: True for sunrise-like times, False for sunset-like times

    Examples:
        >>> # Calculate sunrise with default
        >>> calc = ZmanCalculation(
        ...     method=ZmanMethod(degrees=0.0),
        ...     default_zenith=90.833,
        ...     is_rising=True
        ... )

        >>> # Calculate with custom 16.1° degrees (Alot HaShachar)
        >>> calc = ZmanCalculation(
        ...     method=ZmanMethod(degrees=16.1),
        ...     default_zenith=106.1,
        ...     is_rising=True
        ... )
    """

    method: ZmanMethod
    default_zenith: float
    is_rising: bool


class ZmanDefaults:  # pylint: disable=too-few-public-methods
    """
    Default zenith angles and calculation values for zmanim.

    These represent standard astronomical and halachic values used when
    no custom configuration is provided. All zenith angles are in degrees.

    Zenith angles:
        - 90.0° = True geometric horizon
        - 90.833° = Standard sunrise/sunset (accounts for sun's radius and refraction)
        - Values > 90° indicate sun is below horizon (depression angle)
    """

    # Sunrise/Sunset (accounting for sun's radius and atmospheric refraction)
    NETZ_SHKIA_ZENITH = 90.833  # 90° + 0.833° (0.266° radius + 0.567° refraction)

    # Dawn calculations (degrees below horizon)
    ALOT_ZENITH = 106.1  # GRA standard: 16.1° below horizon

    # Misheyakir (earliest talit/tefillin time)
    MISHEYAKIR_ZENITH = 101.0  # 11° below horizon

    # Nightfall calculations
    TZAIT_ZENITH = 98.5  # GRA standard: 8.5° below horizon (3 medium stars)
    TZAIT_FAST_ZENITH = 96.45  # Slightly earlier for fast days


class ZmanMethodPresets:  # pylint: disable=too-few-public-methods
    """
    Predefined calculation methods for individual zmanim.

    These presets represent calculation methods used by various halachic
    authorities. Use these with ZmanimConfig to build community-specific
    configurations.

    Degree-based calculations (used for astronomical precision):
        ALOT_16_1_DEGREES: GRA standard for Alot HaShachar
        ALOT_16_DEGREES: Slightly less stringent Alot
        ALOT_18_DEGREES: Very stringent (used in polar regions)
        ALOT_19_8_DEGREES: Alternative astronomical calculation
        MISHEYAKIR_10_2_DEGREES: Standard Misheyakir
        MISHEYAKIR_11_DEGREES: More stringent Misheyakir
        TZAIT_8_5_DEGREES: GRA standard for Tzait (3 medium stars)
        TZAIT_7_08_DEGREES: 3 small stars (R' Moshe Feinstein)

    Minute-based calculations (used for practical simplicity):
        ALOT_72_MINUTES: Magen Avraham standard for Alot
        ALOT_90_MINUTES: Stringent Alot calculation
        TZAIT_40_MINUTES: Fast, simple calculation
        TZAIT_42_MINUTES: Common Ashkenazi standard
        TZAIT_50_MINUTES: Stringent calculation (Mishnah Berurah)
        TZAIT_72_MINUTES: Magen Avraham standard
        TZAIT_RABEINU_TAM: Rabeinu Tam's very late opinion

        CANDLE_18_MINUTES: Standard Chutz-L'aaretz (18 minutes)
        CANDLE_20_MINUTES: Standard Israel (20 minutes)
        CANDLE_30_MINUTES: Haifa (30 minutes)
        CANDLE_40_MINUTES: Jerusalem (40 minutes)
    """

    # Alot HaShachar (dawn) calculations
    ALOT_16_1_DEGREES = ZmanMethod(degrees=16.1)
    ALOT_16_DEGREES = ZmanMethod(degrees=16.0)
    ALOT_18_DEGREES = ZmanMethod(degrees=18.0)
    ALOT_19_8_DEGREES = ZmanMethod(degrees=19.8)
    ALOT_72_MINUTES = ZmanMethod(minutes=72)
    ALOT_90_MINUTES = ZmanMethod(minutes=90)

    # Misheyakir (when it becomes light) calculations
    MISHEYAKIR_10_2_DEGREES = ZmanMethod(degrees=10.2)
    MISHEYAKIR_11_DEGREES = ZmanMethod(degrees=11.0)

    # Netz/Shkia zenith
    NETZ_90_833_DEGREES = ZmanMethod(degrees=0.833)
    SHKIA_90_833_DEGREES = ZmanMethod(degrees=0.833)

    # Tzait HaKochavim (nightfall) calculations
    TZAIT_8_5_DEGREES = ZmanMethod(degrees=8.5)
    TZAIT_FAST_6_45_DEGREES = ZmanMethod(degrees=6.45)
    TZAIT_7_08_DEGREES = ZmanMethod(degrees=7.08)
    TZAIT_40_MINUTES = ZmanMethod(minutes=40)
    TZAIT_42_MINUTES = ZmanMethod(minutes=42)
    TZAIT_50_MINUTES = ZmanMethod(minutes=50)
    TZAIT_72_MINUTES = ZmanMethod(minutes=72)
    TZAIT_RABEINU_TAM = ZmanMethod(minutes=72)

    # Candle lighting (all minute-based, no degrees allowed)
    CANDLE_18_MINUTES = ZmanMethod(minutes=18)
    CANDLE_20_MINUTES = ZmanMethod(minutes=20)
    CANDLE_30_MINUTES = ZmanMethod(minutes=30)
    CANDLE_40_MINUTES = ZmanMethod(minutes=40)


@dataclass(frozen=True)
class ZmanimConfig:  # pylint: disable=too-many-instance-attributes
    """
    Configuration for zmanim calculation methods.

    This configuration specifies how to calculate the fundamental times from
    which all other zmanim are derived. The calculation_method determines
    the base for proportional calculations (shaot zmaniyot).

    Attributes:
        calculation_method: Method for calculating proportional times
            (GRA or MGA). This determines whether times are calculated from
            sunrise-to-sunset or from dawn-to-nightfall.

        use_elevation: Whether to adjust sunrise/sunset for observer's elevation.
            When True, applies geometric "dip of horizon" correction based on
            location altitude. Default False for backward compatibility and
            traditional halachic approach (sea-level calculations).

        candle_lighting: Time before sunset to light candles for Shabbat/Yom Tov.
            Typically specified as minutes before sunset.
            Common values: 18 minutes (standard), 20-40 minutes (stricter).

        alot_hashachar: Dawn - when the first light appears in the sky.
            Common values:
            - 16.1 degrees (GRA standard)
            - 72 minutes before sunrise (Magen Avraham)
            - 90 minutes before sunrise (stringent)

        misheyakir: When it becomes light enough to recognize a friend.
            Also the earliest time to put on Tallit and Tefillin.
            Common values:
            - 10.2 degrees (standard)
            - 11.0 degrees (more stringent)

        netz_hachama: Sunrise - when the sun appears on horizon.
            Usually calculated astronomically, rarely customized.
            When use_elevation=True, adjusted for observer's altitude.

        shkia: Sunset - when the sun disappears below horizon.
            Usually calculated astronomically, rarely customized.
            When use_elevation=True, adjusted for observer's altitude.
            Common custom: Some use 0.833° (astronomical), others use different values.

        chatzot: Midday/noon - exact middle point of the day.
            Usually calculated astronomically, rarely customized.

        tzait_hakochavim: When stars appear (nightfall) - regular days.
            Common values:
            - 8.5 degrees (GRA degree-based)
            - 40 minutes after sunset
            - 42 minutes after sunset
            - 50 minutes after sunset (Mishnah Berurah)
            - 72 minutes after sunset (Magen Avraham)

        tzait_fast_day: End of fast day (Tisha B'Av, Yom Kippur, etc).
            Often more stringent than regular tzait. If None, uses tzait_hakochavim.
            Common values:
            - 50 minutes after sunset
            - 72 minutes after sunset

        tzait_shabbat: End of Shabbat/Yom Tov - more stringent than weekday.
            Used for Motzei Shabbat and determining when Shabbat ends.
            If None, uses tzait_hakochavim.
            Common values:
            - 8.5 degrees (3 medium-sized stars)
            - 42 minutes after sunset
            - 50 minutes after sunset
            - 72 minutes after sunset

    Note: Derived times (sof_zman_shema, sof_zman_tfilla, mincha_*, plag_hamincha)
    are calculated from these fundamental times and the shaot zmaniyot calculation,
    which is determined by calculation_method. They are not configurable here.

    Example:
        >>> # GRA-based configuration
        >>> config = ZmanimConfig(
        ...     calculation_method=CalculationMethod.GRA,
        ...     alot_hashachar=ZmanMethod(degrees=16.1),
        ...     tzait_hakochavim=ZmanMethod(degrees=8.5),
        ... )

        >>> # Magen Avraham-based configuration
        >>> config = ZmanimConfig(
        ...     calculation_method=CalculationMethod.MGA,
        ...     alot_hashachar=ZmanMethod(minutes=72),
        ...     tzait_hakochavim=ZmanMethod(minutes=72),
        ... )

        >>> # Custom with different fast day time
        >>> config = ZmanimConfig(
        ...     calculation_method=CalculationMethod.GRA,
        ...     alot_hashachar=ZmanMethod(degrees=16.1),
        ...     tzait_hakochavim=ZmanMethod(minutes=42),
        ...     tzait_fast_day=ZmanMethod(minutes=50),
        ...     tzait_shabbat=ZmanMethod(minutes=50),
        ... )
    """

    # Fundamental calculation method
    calculation_method: CalculationMethod = CalculationMethod.GRA

    # Elevation adjustment
    use_elevation: bool = False

    # Candle lighting (before sunset)
    candle_lighting: ZmanMethod = field(
        default_factory=lambda: ZmanMethodPresets.CANDLE_18_MINUTES
    )

    alot_hashachar: ZmanMethod = field(
        default_factory=lambda: ZmanMethodPresets.ALOT_16_1_DEGREES
    )
    misheyakir: ZmanMethod = field(
        default_factory=lambda: ZmanMethodPresets.MISHEYAKIR_11_DEGREES
    )
    netz_hachama: ZmanMethod = field(
        default_factory=lambda: ZmanMethodPresets.NETZ_90_833_DEGREES
    )
    shkia: ZmanMethod = field(
        default_factory=lambda: ZmanMethodPresets.SHKIA_90_833_DEGREES
    )

    tzait_hakochavim: ZmanMethod = field(
        default_factory=lambda: ZmanMethodPresets.TZAIT_8_5_DEGREES
    )
    tzait_fast_day: ZmanMethod = field(
        default_factory=lambda: ZmanMethodPresets.TZAIT_FAST_6_45_DEGREES
    )
    tzait_shabbat: ZmanMethod = field(
        default_factory=lambda: ZmanMethodPresets.TZAIT_8_5_DEGREES
    )

    def get_calculation(
        self,
        zman_type: ZmanType,
    ) -> ZmanCalculation:
        """
        Create a ZmanCalculation object for the given zman type.

        This looks up the configured method and default parameters for the
        specified zman type and returns a complete ZmanCalculation object.

        Args:
            zman_type: The type of zman to calculate (e.g., ZmanType.NETZ_HACHAMA)

        Returns:
            ZmanCalculation object ready to pass to Zmanim._get_configured_time()

        Example:
            >>> config = ZmanimConfig(calculation_method=CalculationMethod.GRA)
            >>> calc = config.get_calculation(ZmanType.NETZ_HACHAMA)
        """
        # Map zman types to their configuration and default parameters
        zman_params = {
            ZmanType.NETZ_HACHAMA: (
                self.netz_hachama,
                ZmanDefaults.NETZ_SHKIA_ZENITH,
                True,
            ),
            ZmanType.SHKIA: (self.shkia, ZmanDefaults.NETZ_SHKIA_ZENITH, False),
            ZmanType.ALOT_HASHACHAR: (
                self.alot_hashachar,
                ZmanDefaults.ALOT_ZENITH,
                True,
            ),
            ZmanType.MISHEYAKIR: (
                self.misheyakir,
                ZmanDefaults.MISHEYAKIR_ZENITH,
                True,
            ),
            ZmanType.TZAIT_HAKOCHAVIM: (
                self.tzait_hakochavim,
                ZmanDefaults.TZAIT_ZENITH,
                False,
            ),
            ZmanType.TZAIT_FAST_DAY: (
                self.tzait_fast_day,
                ZmanDefaults.TZAIT_FAST_ZENITH,
                False,
            ),
            ZmanType.TZAIT_SHABBAT: (
                self.tzait_shabbat,
                ZmanDefaults.TZAIT_ZENITH,
                False,
            ),
        }

        zman_method, default_zenith, is_rising = zman_params[zman_type]

        return ZmanCalculation(
            method=zman_method,
            default_zenith=default_zenith,
            is_rising=is_rising,
        )

    def __post_init__(self) -> None:
        """Validate configuration."""
        if not isinstance(self.calculation_method, CalculationMethod):
            raise ValueError(
                f"calculation_method must be a CalculationMethod enum, "
                f"got {type(self.calculation_method)}"
            )

        # Candle lighting must use minutes, not degrees
        if self.candle_lighting.degrees is not None:
            raise ValueError(
                "Candle lighting must be specified in minutes (e.g., 18 minutes "
                "before sunset), not degrees. Use "
                "ZmanMethodPresets.CANDLE_18_MINUTES or similar."
            )


class ZmanimPresets:
    """
    Predefined zmanim configurations for different communities and authorities.

    These presets represent complete calculation methods used by various
    communities worldwide. Each preset configures how all zmanim are calculated
    according to that community's custom (minhag).

    Available presets:
        gra_standard(): Vilna Gaon method - degree-based calculations
        mga_standard(): Magen Avraham method - minute-based calculations
        jerusalem_standard(): Jerusalem custom
        israeli_standard(): Israeli standard times
        sephardic_standard(): Sephardic Jewish custom
        chazon_ish(): Chazon Ish method
        rabeinu_tam(): Very late Tzait (for Havdalah)
    """

    @staticmethod
    def gra_standard() -> ZmanimConfig:
        """
        Vilna Gaon (GRA) standard calculation method.

        Uses degree-based calculations:
        - Alot: 16.1 degrees below horizon
        - Misheyakir: 11 degrees below horizon
        - Tzait: 8.5 degrees below horizon
        - Tzait (fast day): 6.45 degrees below horizon
        - Sunrise-to-sunset proportional calculations

        This is the most common Ashkenazi method.
        """
        return ZmanimConfig(
            calculation_method=CalculationMethod.GRA,
            candle_lighting=ZmanMethodPresets.CANDLE_18_MINUTES,
            alot_hashachar=ZmanMethodPresets.ALOT_16_1_DEGREES,
            misheyakir=ZmanMethodPresets.MISHEYAKIR_11_DEGREES,
            tzait_hakochavim=ZmanMethodPresets.TZAIT_8_5_DEGREES,
            tzait_fast_day=ZmanMethodPresets.TZAIT_FAST_6_45_DEGREES,
            tzait_shabbat=ZmanMethodPresets.TZAIT_8_5_DEGREES,
        )

    @staticmethod
    def mga_standard() -> ZmanimConfig:
        """
        Magen Avraham (MGA) standard calculation method.

        Uses minute-based calculations:
        - Alot: 72 minutes before sunrise
        - Tzait: 72 minutes after sunset
        - Dawn-to-nightfall proportional calculations

        Named after Rabbi Avraham Abele Gombiner. MGA and Baal HaTanya
        methods are equivalent for calculation purposes.
        """
        return ZmanimConfig(
            calculation_method=CalculationMethod.MGA,
            candle_lighting=ZmanMethodPresets.CANDLE_18_MINUTES,
            alot_hashachar=ZmanMethodPresets.ALOT_72_MINUTES,
            tzait_hakochavim=ZmanMethodPresets.TZAIT_72_MINUTES,
            tzait_shabbat=ZmanMethodPresets.TZAIT_72_MINUTES,
        )

    @staticmethod
    def jerusalem_standard() -> ZmanimConfig:
        """
        Conservative Jerusalem-based custom.

        Conservative with degree-based calculations.
        Often used for very stringent Shabbat times.
        """
        return ZmanimConfig(
            calculation_method=CalculationMethod.GRA,
            candle_lighting=ZmanMethodPresets.CANDLE_20_MINUTES,
            alot_hashachar=ZmanMethodPresets.ALOT_16_1_DEGREES,
            misheyakir=ZmanMethodPresets.MISHEYAKIR_10_2_DEGREES,
            tzait_hakochavim=ZmanMethodPresets.TZAIT_8_5_DEGREES,
            tzait_shabbat=ZmanMethodPresets.TZAIT_8_5_DEGREES,
            tzait_fast_day=ZmanMethodPresets.TZAIT_8_5_DEGREES,
        )

    @staticmethod
    def israeli_standard() -> ZmanimConfig:
        """
        Standard Israeli calculation method.

        Practical minute-based calculations commonly used in Israel.
        """
        return ZmanimConfig(
            calculation_method=CalculationMethod.GRA,
            candle_lighting=ZmanMethodPresets.CANDLE_18_MINUTES,
            alot_hashachar=ZmanMethodPresets.ALOT_72_MINUTES,
            tzait_hakochavim=ZmanMethodPresets.TZAIT_42_MINUTES,
            tzait_shabbat=ZmanMethodPresets.TZAIT_50_MINUTES,
        )

    @staticmethod
    def sephardic_standard() -> ZmanimConfig:
        """
        Standard Sephardic Jewish custom.

        Often less stringent than Ashkenazi for evening times.
        """
        return ZmanimConfig(
            calculation_method=CalculationMethod.GRA,
            candle_lighting=ZmanMethodPresets.CANDLE_18_MINUTES,
            alot_hashachar=ZmanMethodPresets.ALOT_16_1_DEGREES,
            tzait_hakochavim=ZmanMethodPresets.TZAIT_40_MINUTES,
            tzait_shabbat=ZmanMethodPresets.TZAIT_42_MINUTES,
        )

    @staticmethod
    def chazon_ish() -> ZmanimConfig:
        """
        Chazon Ish method - very stringent calculation.

        Known for strict interpretation of halachic times.
        Uses degree-based calculations with stringent values.
        """
        return ZmanimConfig(
            calculation_method=CalculationMethod.GRA,
            candle_lighting=ZmanMethodPresets.CANDLE_20_MINUTES,
            alot_hashachar=ZmanMethodPresets.ALOT_18_DEGREES,
            misheyakir=ZmanMethodPresets.MISHEYAKIR_11_DEGREES,
            tzait_hakochavim=ZmanMethodPresets.TZAIT_8_5_DEGREES,
            tzait_shabbat=ZmanMethodPresets.TZAIT_8_5_DEGREES,
            tzait_fast_day=ZmanMethodPresets.TZAIT_50_MINUTES,
        )

    @staticmethod
    def rabeinu_tam() -> ZmanimConfig:
        """
        Very late Tzait - used for late Havdalah.

        Rabeinu Tam's stringent interpretation: 72 minutes after sunset.
        """
        return ZmanimConfig(
            calculation_method=CalculationMethod.MGA,
            candle_lighting=ZmanMethodPresets.CANDLE_18_MINUTES,
            alot_hashachar=ZmanMethodPresets.ALOT_72_MINUTES,
            tzait_hakochavim=ZmanMethodPresets.TZAIT_72_MINUTES,
            tzait_shabbat=ZmanMethodPresets.TZAIT_72_MINUTES,
        )


def create_custom_config(**kwargs: Any) -> ZmanimConfig:
    """
    Create a custom ZmanimConfig with flexible pythonic syntax.

    This helper function allows creating configurations using keyword arguments,
    automatically converting string method names to CalculationMethod enum values
    and validating field names.

    Parameters:
        calculation_method: "gra", "baal_hatanya", or "mga" (auto-converted to
            CalculationMethod)
        alot_hashachar: ZmanMethod(...) or None
        misheyakir: ZmanMethod(...) or None
        netz_hachama: ZmanMethod(...) or None
        chatzot: ZmanMethod(...) or None
        tzait_hakochavim: ZmanMethod(...) or None
        tzait_fast_day: ZmanMethod(...) or None
        tzait_shabbat: ZmanMethod(...) or None

    Returns:
        ZmanimConfig instance with specified values

    Raises:
        ValueError: If invalid field name or calculation_method provided

    Examples:
        >>> # Create GRA-based configuration
        >>> config = create_custom_config(
        ...     calculation_method="gra",
        ...     alot_hashachar=ZmanMethod(degrees=16.1),
        ...     tzait_hakochavim=ZmanMethod(degrees=8.5),
        ... )

        >>> # Create MGA-based configuration
        >>> config = create_custom_config(
        ...     calculation_method="mga",
        ...     alot_hashachar=ZmanMethod(minutes=72),
        ...     tzait_hakochavim=ZmanMethod(minutes=72),
        ... )

        >>> # Create custom with different fast day time
        >>> config = create_custom_config(
        ...     calculation_method="gra",
        ...     alot_hashachar=ZmanMethod(degrees=16.1),
        ...     tzait_hakochavim=ZmanMethod(minutes=42),
        ...     tzait_fast_day=ZmanMethod(minutes=50),
        ... )
    """
    # Normalize calculation_method string to enum
    config_dict = dict(kwargs)
    if "calculation_method" in config_dict:
        method = config_dict["calculation_method"]
        if isinstance(method, str):
            method_upper = method.upper()
            try:
                config_dict["calculation_method"] = CalculationMethod[method_upper]
            except KeyError as exc:
                raise ValueError(
                    f"Invalid calculation_method '{method}'. "
                    f"Must be 'gra' or 'mga'."
                ) from exc

    # Get all valid ZmanimConfig field names
    valid_fields = {
        "calculation_method",
        "use_elevation",
        "candle_lighting",
        "alot_hashachar",
        "misheyakir",
        "netz_hachama",
        "shkia",
        "chatzot",
        "tzait_hakochavim",
        "tzait_fast_day",
        "tzait_shabbat",
    }

    # Validate field names
    invalid_fields = set(config_dict.keys()) - valid_fields
    if invalid_fields:
        raise ValueError(
            f"Invalid field(s) for ZmanimConfig: {', '.join(invalid_fields)}. "
            f"Valid fields are: {', '.join(sorted(valid_fields))}"
        )

    return ZmanimConfig(**config_dict)
