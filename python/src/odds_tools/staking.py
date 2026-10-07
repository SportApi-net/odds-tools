"""Expected value and the Kelly criterion."""

from __future__ import annotations

from ._validate import OddsError, decimal_odds, non_negative, number
from ._validate import probability as _probability


def expected_value(odds: float, probability: float, stake: float = 1.0) -> float:
    """Expected profit of a bet: ``stake * (p * d - 1)``.

    With the default ``stake=1`` this is the edge (ROI per unit staked):
    ``expected_value(2.1, 0.5)`` is ``0.05`` (+5 %, up to float rounding).
    """
    d = decimal_odds(odds)
    p = _probability(probability)
    amount = non_negative(stake, "stake")
    return amount * (p * d - 1)


def kelly_fraction(odds: float, probability: float, fraction: float = 1.0) -> float:
    """Share of the bankroll to stake according to the Kelly criterion.

    Full Kelly is ``f* = (b * p - q) / b = (p * d - 1) / (d - 1)`` where
    ``b = d - 1`` and ``q = 1 - p``. The result is multiplied by ``fraction``
    (``0.5`` = half Kelly). Returns ``0`` when the bet has no positive edge -
    Kelly never recommends backing a negative-EV price.
    """
    d = decimal_odds(odds)
    p = _probability(probability)
    share = number(fraction, "fraction")
    if not 0 < share <= 1:
        raise OddsError(f"fraction must be in (0, 1] (got {fraction!r})")
    full = (p * d - 1) / (d - 1)
    if full <= 0:
        return 0.0
    return full * share


def kelly_stake(bankroll: float, odds: float, probability: float, fraction: float = 1.0) -> float:
    """Kelly stake in money: ``bankroll * kelly_fraction(odds, probability, fraction)``."""
    amount = non_negative(bankroll, "bankroll")
    return amount * kelly_fraction(odds, probability, fraction)
