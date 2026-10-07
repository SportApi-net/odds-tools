"""Conversions between odds formats and implied probability.

Decimal odds are the hub format: every converter goes through them.

=============  ===========================  ===========================
Format         From decimal ``d``           Valid values
=============  ===========================  ===========================
fractional     ``d - 1`` as ``"n/m"``       ``n > 0``, ``m > 0``
american       ``(d-1)*100`` if ``d >= 2``  ``>= +100`` or ``<= -100``
               else ``-100/(d-1)``
hongkong       ``d - 1``                    ``> 0``
indonesian     ``d - 1`` if ``d >= 2``      ``>= 1`` or ``<= -1``
               else ``-1/(d-1)``
malay          ``d - 1`` if ``d <= 2``      ``(0, 1]`` or ``[-1, 0)``
               else ``-1/(d-1)``
probability    ``1 / d``                    ``(0, 1)``
=============  ===========================  ===========================
"""

from __future__ import annotations

import re
from fractions import Fraction
from typing import Literal, Union, overload

from ._validate import OddsError, decimal_odds, integer, number
from .rounding import round_half_up

FORMATS = (
    "decimal",
    "fractional",
    "american",
    "hongkong",
    "indonesian",
    "malay",
    "probability",
)

OddsValue = Union[float, str]
NumericFormat = Literal["decimal", "american", "hongkong", "indonesian", "malay", "probability"]

_FRACTION_RE = re.compile(r"^\s*(\d+)\s*/\s*(\d+)\s*$")
_EVENS = {"evens", "evs", "even"}


# --- fractional -------------------------------------------------------------


def fractional_to_decimal(fraction: str) -> float:
    """``"5/2"`` -> ``3.5``. ``"evens"`` (or ``"evs"``) is accepted as ``"1/1"``."""
    if not isinstance(fraction, str):
        raise OddsError(f"fractional odds must be a string like '5/2' (got {fraction!r})")
    if fraction.strip().lower() in _EVENS:
        return 2.0
    match = _FRACTION_RE.match(fraction)
    if match is None:
        raise OddsError(f"fractional odds must look like '5/2' (got {fraction!r})")
    numerator, denominator = int(match.group(1)), int(match.group(2))
    if numerator == 0 or denominator == 0:
        raise OddsError(
            f"fractional odds need a positive numerator and denominator (got {fraction!r})"
        )
    return 1 + numerator / denominator


def decimal_to_fractional(odds: float, max_denominator: int = 100) -> str:
    """``3.5`` -> ``"5/2"``.

    The decimal price is read as written (``1.91`` is exactly 191/100), reduced,
    and - if its denominator exceeds ``max_denominator`` - replaced by the
    closest fraction whose denominator is at most ``max_denominator``.
    Raises :class:`OddsError` if that closest fraction would be ``0/1``
    (prices extremely close to 1); pass a larger ``max_denominator`` then.
    """
    d = decimal_odds(odds)
    limit = integer(max_denominator, "max_denominator")
    if limit < 1:
        raise OddsError(f"max_denominator must be at least 1 (got {max_denominator!r})")
    profit = Fraction(repr(d)) - 1
    if profit.denominator > limit:
        profit = profit.limit_denominator(limit)
    if profit.numerator == 0:
        raise OddsError(f"odds {d!r} cannot be written as a fraction with denominator <= {limit}")
    return f"{profit.numerator}/{profit.denominator}"


# --- american (moneyline) ---------------------------------------------------


def american_to_decimal(american: float) -> float:
    """``+150`` -> ``2.5``; ``-200`` -> ``1.5``. Values between -100 and +100 are invalid."""
    a = number(american, "american odds")
    if a >= 100:
        return 1 + a / 100
    if a <= -100:
        return 1 + 100 / -a
    raise OddsError(f"american odds must be >= +100 or <= -100 (got {american!r})")


def decimal_to_american(odds: float) -> float:
    """``2.5`` -> ``150.0``; ``1.5`` -> ``-200.0``. Even money (2.0) is ``+100``."""
    d = decimal_odds(odds)
    if d >= 2:
        return (d - 1) * 100
    return -100 / (d - 1)


def format_american(american: float, decimals: int = 0) -> str:
    """Format a moneyline price with an explicit sign: ``150`` -> ``"+150"``."""
    a = number(american, "american odds")
    if -100 < a < 100:
        raise OddsError(f"american odds must be >= +100 or <= -100 (got {american!r})")
    rounded = round_half_up(a, decimals)
    text = f"{abs(rounded):.{decimals}f}"
    return ("+" if rounded > 0 else "-") + text


# --- Asian formats ----------------------------------------------------------


def hongkong_to_decimal(hongkong: float) -> float:
    """Hong Kong odds are the net profit per unit staked: ``1.5`` -> ``2.5``."""
    h = number(hongkong, "hong kong odds")
    if h <= 0:
        raise OddsError(f"hong kong odds must be greater than 0 (got {hongkong!r})")
    return 1 + h


def decimal_to_hongkong(odds: float) -> float:
    return decimal_odds(odds) - 1


def indonesian_to_decimal(indonesian: float) -> float:
    """Indonesian odds are American odds divided by 100: ``-2.0`` -> ``1.5``."""
    i = number(indonesian, "indonesian odds")
    if i >= 1:
        return 1 + i
    if i <= -1:
        return 1 + 1 / -i
    raise OddsError(f"indonesian odds must be >= 1 or <= -1 (got {indonesian!r})")


def decimal_to_indonesian(odds: float) -> float:
    d = decimal_odds(odds)
    if d >= 2:
        return d - 1
    return -1 / (d - 1)


def malay_to_decimal(malay: float) -> float:
    """Malay odds: positive values in (0, 1], negative values in [-1, 0)."""
    m = number(malay, "malay odds")
    if 0 < m <= 1:
        return 1 + m
    if -1 <= m < 0:
        return 1 + 1 / -m
    raise OddsError(f"malay odds must be in (0, 1] or [-1, 0) (got {malay!r})")


def decimal_to_malay(odds: float) -> float:
    d = decimal_odds(odds)
    if d <= 2:
        return d - 1
    return -1 / (d - 1)


# --- probability ------------------------------------------------------------


def implied_probability(odds: float) -> float:
    """Raw implied probability ``1 / d`` (still includes the bookmaker margin)."""
    return 1 / decimal_odds(odds)


def probability_to_decimal(probability: float) -> float:
    """``0.4`` -> ``2.5``. The probability must be strictly between 0 and 1."""
    p = number(probability, "probability")
    if not 0 < p < 1:
        raise OddsError(f"probability must be strictly between 0 and 1 (got {probability!r})")
    return 1 / p


# --- generic ----------------------------------------------------------------


def to_decimal(value: OddsValue, from_format: str) -> float:
    """Convert a price in ``from_format`` (one of :data:`FORMATS`) to decimal odds."""
    fmt = _format(from_format, "from_format")
    if fmt == "decimal":
        return decimal_odds(value)
    if fmt == "fractional":
        return fractional_to_decimal(value)  # type: ignore[arg-type]
    if fmt == "probability":
        return probability_to_decimal(value)  # type: ignore[arg-type]
    return _TO_DECIMAL[fmt](value)  # type: ignore[arg-type]


@overload
def from_decimal(odds: float, to_format: Literal["fractional"]) -> str: ...
@overload
def from_decimal(odds: float, to_format: NumericFormat) -> float: ...
@overload
def from_decimal(odds: float, to_format: str) -> OddsValue: ...
def from_decimal(odds: float, to_format: str) -> OddsValue:
    """Convert decimal odds to ``to_format`` (one of :data:`FORMATS`)."""
    fmt = _format(to_format, "to_format")
    if fmt == "decimal":
        return decimal_odds(odds)
    if fmt == "fractional":
        return decimal_to_fractional(odds)
    if fmt == "probability":
        return implied_probability(odds)
    return _FROM_DECIMAL[fmt](odds)


@overload
def convert(value: OddsValue, from_format: str, to_format: Literal["fractional"]) -> str: ...
@overload
def convert(value: OddsValue, from_format: str, to_format: NumericFormat) -> float: ...
@overload
def convert(value: OddsValue, from_format: str, to_format: str) -> OddsValue: ...
def convert(value: OddsValue, from_format: str, to_format: str) -> OddsValue:
    """Convert a price between any two :data:`FORMATS`.

    >>> convert("3/2", "fractional", "american")
    150.0
    """
    return from_decimal(to_decimal(value, from_format), to_format)


def _format(name: object, argument: str) -> str:
    if not isinstance(name, str) or name not in FORMATS:
        raise OddsError(f"{argument} must be one of {', '.join(FORMATS)} (got {name!r})")
    return name


_TO_DECIMAL = {
    "american": american_to_decimal,
    "hongkong": hongkong_to_decimal,
    "indonesian": indonesian_to_decimal,
    "malay": malay_to_decimal,
}

_FROM_DECIMAL = {
    "american": decimal_to_american,
    "hongkong": decimal_to_hongkong,
    "indonesian": decimal_to_indonesian,
    "malay": decimal_to_malay,
}
