"""Predictable decimal rounding for prices and stakes."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Context, Decimal

from ._validate import OddsError, integer, number

_CONTEXT = Context(prec=400, rounding=ROUND_HALF_UP)


def round_half_up(value: float, decimals: int = 2) -> float:
    """Round ``value`` to ``decimals`` places, halves away from zero.

    Rounding works on the shortest decimal representation of the float (what
    ``repr`` prints), so ``round_half_up(2.675, 2) == 2.68`` - unlike the
    built-in :func:`round`, which returns ``2.67`` because of binary floating
    point and uses banker's rounding.

    >>> round_half_up(1.905)
    1.91
    >>> round_half_up(-0.125, 2)
    -0.13
    """
    x = number(value, "value")
    places = integer(decimals, "decimals")
    if not 0 <= places <= 15:
        raise OddsError(f"decimals must be between 0 and 15 (got {decimals!r})")
    exact = Decimal(repr(x))
    quantum = Decimal(1).scaleb(-places)
    return float(exact.quantize(quantum, context=_CONTEXT))
