"""Bookmaker margin (overround) and fair, no-vig prices.

``odds`` is always the list of decimal prices of *one* market whose outcomes
are mutually exclusive and exhaustive (e.g. 1X2, or both sides of a total).
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from ._validate import OddsError, odds_list, plain_sum

METHODS = ("multiplicative", "additive", "power", "shin")

# Bisection runs a fixed number of steps so that the Python and JavaScript
# packages perform exactly the same operations.
_BISECTION_STEPS = 200


def implied_probabilities(odds: Sequence[float]) -> list[float]:
    """``1 / d`` for every price. They sum to the overround, not to 1."""
    return [1 / d for d in odds_list(odds, 1)]


def overround(odds: Sequence[float]) -> float:
    """Sum of implied probabilities, e.g. ``1.05`` for a 5 % book."""
    return plain_sum(implied_probabilities(odds_list(odds, 2)))


def margin(odds: Sequence[float]) -> float:
    """Bookmaker margin ``overround - 1`` (``0.05`` = 5 %). Negative means arbitrage."""
    return overround(odds) - 1


def market_payout(odds: Sequence[float]) -> float:
    """Theoretical payout (return to player) ``1 / overround``, e.g. ``0.952``."""
    return 1 / overround(odds)


def fair_probabilities(odds: Sequence[float], method: str = "multiplicative") -> list[float]:
    """Remove the margin and return probabilities that sum to 1.

    Methods:

    * ``"multiplicative"`` - ``p_i = pi_i / S`` (normalisation, the common default).
    * ``"additive"`` - ``p_i = pi_i - (S - 1) / n``; equal margin per outcome.
      Raises :class:`OddsError` if a long shot would get ``p <= 0``.
    * ``"power"`` - ``p_i = pi_i ** k`` with ``k`` chosen so the sum is 1.
    * ``"shin"`` - Shin (1993) model of insider trading; corrects the
      favourite-longshot bias. Requires a positive margin.

    where ``pi_i = 1 / d_i`` and ``S = sum(pi_i)``.
    """
    prices = odds_list(odds, 2)
    if not isinstance(method, str) or method not in METHODS:
        raise OddsError(f"method must be one of {', '.join(METHODS)} (got {method!r})")
    implied = [1 / d for d in prices]
    total = plain_sum(implied)
    if method == "multiplicative":
        return [p / total for p in implied]
    if method == "additive":
        return _additive(implied, total)
    if method == "power":
        return _power(implied)
    return _shin(implied, total)


def fair_odds(odds: Sequence[float], method: str = "multiplicative") -> list[float]:
    """Decimal odds without the margin: ``1 / p`` for :func:`fair_probabilities`."""
    return [1 / p for p in fair_probabilities(odds, method)]


def shin_z(odds: Sequence[float]) -> float:
    """Shin's ``z``: the estimated share of money from insiders (0 for a fair book)."""
    prices = odds_list(odds, 2)
    implied = [1 / d for d in prices]
    total = plain_sum(implied)
    _check_shin(total)
    return _solve_shin_z(implied, total)


def _additive(implied: list[float], total: float) -> list[float]:
    share = (total - 1) / len(implied)
    result = [p - share for p in implied]
    for i, p in enumerate(result):
        if p <= 0:
            raise OddsError(
                f"additive method gives a non-positive probability for outcome {i} "
                "(margin is larger than its implied probability); "
                "use 'multiplicative', 'power' or 'shin' instead"
            )
    return result


def _power(implied: list[float]) -> list[float]:
    def excess(k: float) -> float:
        return plain_sum([p**k for p in implied]) - 1

    # excess(k) decreases in k and excess(0) = n - 1 > 0.
    lo, hi = 0.0, 1.0
    while excess(hi) > 0:
        lo, hi = hi, hi * 2
    for _ in range(_BISECTION_STEPS):
        mid = (lo + hi) / 2
        if excess(mid) > 0:
            lo = mid
        else:
            hi = mid
    k = (lo + hi) / 2
    powered = [p**k for p in implied]
    total = plain_sum(powered)
    return [p / total for p in powered]


def _check_shin(total: float) -> None:
    if total < 1:
        raise OddsError(
            "the Shin method needs a market with a positive margin (overround > 1); "
            f"this market has an overround of {total!r}"
        )


def _shin_probabilities(implied: list[float], total: float, z: float) -> list[float]:
    return [(math.sqrt(z * z + 4 * (1 - z) * p * p / total) - z) / (2 * (1 - z)) for p in implied]


def _solve_shin_z(implied: list[float], total: float) -> float:
    if total == 1:
        return 0.0
    # sum(p(z)) - 1 is sqrt(S) - 1 > 0 at z = 0 and tends to
    # sum(pi^2) / S - 1 < 0 as z -> 1, so bisection on [0, 1) finds the root.
    lo, hi = 0.0, 1.0
    for _ in range(_BISECTION_STEPS):
        mid = (lo + hi) / 2
        if mid in (lo, hi):
            break
        if plain_sum(_shin_probabilities(implied, total, mid)) > 1:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _shin(implied: list[float], total: float) -> list[float]:
    _check_shin(total)
    z = _solve_shin_z(implied, total)
    if z == 0:
        return [p / total for p in implied]
    probabilities = _shin_probabilities(implied, total, z)
    norm = plain_sum(probabilities)
    return [p / norm for p in probabilities]
