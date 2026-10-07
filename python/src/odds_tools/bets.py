"""Accumulators (parlays) and system bets."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from itertools import combinations
from math import comb
from typing import Any, Union

from ._validate import OddsError, integer, non_negative, odds_list, plain_sum

RESULTS = ("win", "lose", "void")

Result = Union[str, bool]
Sizes = Union[int, Sequence[int]]


@dataclass(frozen=True)
class SystemBet:
    """Summary of a system bet; see :func:`system_bet`."""

    legs: int
    """Number of selections."""
    sizes: tuple[int, ...]
    """Accumulator sizes included, ascending (``(2,)`` for a 2/3 system)."""
    bets: int
    """Number of combinations (``C(n, k)`` summed over sizes)."""
    unit_stake: float
    """Stake on each combination: ``total_stake / bets``."""
    total_stake: float
    max_payout: float
    """Total return if every selection wins."""


def accumulator_odds(odds: Sequence[float]) -> float:
    """Combined decimal odds of an accumulator: the product of all legs."""
    result = 1.0
    for d in odds_list(odds, 1):
        result *= d
    return result


def accumulator_payout(
    stake: float, odds: Sequence[float], results: Sequence[Result] | None = None
) -> float:
    """Total return of an accumulator (stake included).

    Without ``results`` every leg is assumed to win. With ``results`` (one of
    ``"win"``, ``"lose"``, ``"void"`` - or ``True``/``False`` - per leg), a
    lost leg makes the payout 0 and a void leg counts as odds of 1.
    """
    amount = non_negative(stake, "stake")
    prices = odds_list(odds, 1)
    factors = prices if results is None else _factors(prices, results)
    result = amount
    for f in factors:
        result *= f
    return result


def system_combinations(legs: int, sizes: Sizes) -> list[tuple[int, ...]]:
    """All leg-index combinations of a system, smallest size first.

    >>> system_combinations(3, 2)
    [(0, 1), (0, 2), (1, 2)]
    """
    n = integer(legs, "legs")
    if n < 1:
        raise OddsError(f"legs must be at least 1 (got {legs!r})")
    return [c for k in _sizes(sizes, n) for c in combinations(range(n), k)]


def system_bet(odds: Sequence[float], sizes: Sizes, total_stake: float) -> SystemBet:
    """Describe a system bet: number of bets, stake split and maximum payout.

    ``sizes`` is the accumulator size (``2`` for a 2/3 system) or a list of
    sizes for full-cover bets (``[2, 3, 4]`` on 4 legs is a Yankee, 11 bets).
    ``total_stake`` is split equally across all combinations.
    """
    prices = odds_list(odds, 1)
    ks = _sizes(sizes, len(prices))
    stake = non_negative(total_stake, "total_stake")
    bets = sum(comb(len(prices), k) for k in ks)
    unit = stake / bets
    return SystemBet(
        legs=len(prices),
        sizes=ks,
        bets=bets,
        unit_stake=unit,
        total_stake=stake,
        max_payout=unit * _combination_sum(prices, ks),
    )


def system_payout(
    odds: Sequence[float], sizes: Sizes, total_stake: float, results: Sequence[Result]
) -> float:
    """Total return of a system bet once results are known.

    Each combination pays ``unit_stake * product(odds)`` if none of its legs
    lost (void legs count as odds of 1, so an all-void combination returns its
    stake) and 0 otherwise. Combinations are never enumerated: the sum over
    all ``k``-leg subsets is the elementary symmetric polynomial ``e_k``.
    """
    bet = system_bet(odds, sizes, total_stake)
    factors = _factors(odds_list(odds, 1), results)
    return bet.unit_stake * _combination_sum(factors, bet.sizes)


def _combination_sum(factors: Sequence[float], sizes: Sequence[int]) -> float:
    """Sum over k in sizes of e_k(factors) (sum of products of all k-subsets)."""
    top = max(sizes)
    e = [1.0] + [0.0] * top
    for f in factors:
        for k in range(top, 0, -1):
            e[k] += e[k - 1] * f
    return plain_sum([e[k] for k in sizes])


def _sizes(sizes: Any, legs: int) -> tuple[int, ...]:
    raw = [sizes] if not isinstance(sizes, (list, tuple)) else list(sizes)
    if not raw:
        raise OddsError("sizes must not be empty")
    values = sorted({integer(k, "size") for k in raw})
    for k in values:
        if not 1 <= k <= legs:
            raise OddsError(f"system size must be between 1 and {legs} (got {k})")
    return tuple(values)


def _factors(prices: list[float], results: Any) -> list[float]:
    if isinstance(results, (str, bytes)) or not isinstance(results, Sequence):
        raise OddsError(f"results must be a list with one entry per leg (got {results!r})")
    if len(results) != len(prices):
        raise OddsError(f"results must have one entry per leg ({len(prices)}), got {len(results)}")
    factors = []
    for i, (price, result) in enumerate(zip(prices, results)):
        if result is True or result == "win":
            factors.append(price)
        elif result is False or result == "lose":
            factors.append(0.0)
        elif result == "void":
            factors.append(1.0)
        else:
            raise OddsError(
                f"results[{i}] must be 'win', 'lose', 'void', True or False (got {result!r})"
            )
    return factors
