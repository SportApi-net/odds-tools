"""Input validation shared by every public function.

All public functions raise :class:`OddsError` (a :class:`ValueError` subclass)
for invalid input, so callers only need to catch one exception type.
"""

from __future__ import annotations

import math
import numbers
from collections.abc import Sequence
from typing import Any


class OddsError(ValueError):
    """Raised when an argument is not a valid price, probability, stake or option."""


def number(value: Any, name: str) -> float:
    """Return ``value`` as a finite float or raise :class:`OddsError`."""
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise OddsError(f"{name} must be a number (got {value!r})")
    result = float(value)
    if not math.isfinite(result):
        raise OddsError(f"{name} must be a finite number (got {value!r})")
    return result


def integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, numbers.Integral):
        raise OddsError(f"{name} must be an integer (got {value!r})")
    return int(value)


def decimal_odds(value: Any, name: str = "odds") -> float:
    """Decimal odds must be a finite number strictly greater than 1."""
    result = number(value, name)
    if result <= 1:
        raise OddsError(f"{name} must be greater than 1 (got {value!r})")
    return result


def odds_list(values: Any, min_length: int, name: str = "odds") -> list[float]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise OddsError(f"{name} must be a list of decimal odds (got {values!r})")
    if len(values) < min_length:
        raise OddsError(f"{name} must contain at least {min_length} price(s) (got {len(values)})")
    return [decimal_odds(v, f"{name}[{i}]") for i, v in enumerate(values)]


def probability(value: Any, name: str = "probability") -> float:
    """A probability in the closed interval [0, 1]."""
    result = number(value, name)
    if not 0 <= result <= 1:
        raise OddsError(f"{name} must be between 0 and 1 (got {value!r})")
    return result


def non_negative(value: Any, name: str) -> float:
    result = number(value, name)
    if result < 0:
        raise OddsError(f"{name} must not be negative (got {value!r})")
    return result


def positive(value: Any, name: str) -> float:
    result = number(value, name)
    if result <= 0:
        raise OddsError(f"{name} must be greater than 0 (got {value!r})")
    return result


def plain_sum(values: Sequence[float]) -> float:
    """Left-to-right float sum.

    Used instead of :func:`sum` because CPython 3.12+ switched ``sum`` to
    compensated summation; a plain loop gives identical results on every
    supported Python version and in the JavaScript package.
    """
    total = 0.0
    for v in values:
        total += v
    return total
