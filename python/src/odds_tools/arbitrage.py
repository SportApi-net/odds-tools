"""Arbitrage (surebet) detection and stake distribution."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from ._validate import odds_list, plain_sum, positive
from .rounding import round_half_up


@dataclass(frozen=True)
class Arbitrage:
    """Result of :func:`arbitrage`."""

    is_arbitrage: bool
    """True when the best prices sum to an overround below 1."""
    overround: float
    """Sum of ``1 / d`` over the outcomes."""
    profit_margin: float
    """Theoretical return on the total stake, ``1 / overround - 1``."""
    total_stake: float
    """Sum of :attr:`stakes` (differs from the requested amount after rounding)."""
    stakes: tuple[float, ...]
    payouts: tuple[float, ...]
    """Return for each outcome if it wins: ``stake * odds``."""
    profit: float
    """Guaranteed profit: ``min(payouts) - total_stake`` (negative if not an arbitrage)."""


def is_arbitrage(odds: Sequence[float]) -> bool:
    """True if backing every outcome at these prices guarantees a profit."""
    return plain_sum([1 / d for d in odds_list(odds, 2)]) < 1


def arbitrage(odds: Sequence[float], total_stake: float, decimals: int | None = None) -> Arbitrage:
    """Split ``total_stake`` across the outcomes so every outcome returns the same.

    ``odds`` are the best decimal prices for each outcome of one market (2-way,
    3-way, or more), possibly from different bookmakers. Stakes are
    proportional to ``1 / d``: ``stake_i = total * (1 / d_i) / overround``.

    Pass ``decimals`` (e.g. ``2`` for cents, ``0`` for whole units) to round
    each stake half-up; payouts and profit are then computed from the rounded
    stakes. The function also works for non-arbitrage markets (the profit is
    then negative), which is useful for hedging.
    """
    prices = odds_list(odds, 2)
    amount = positive(total_stake, "total_stake")
    implied = [1 / d for d in prices]
    book = plain_sum(implied)
    stakes = [amount * p / book for p in implied]
    if decimals is not None:
        stakes = [round_half_up(s, decimals) for s in stakes]
    payouts = [s * d for s, d in zip(stakes, prices)]
    staked = plain_sum(stakes)
    return Arbitrage(
        is_arbitrage=book < 1,
        overround=book,
        profit_margin=1 / book - 1,
        total_stake=staked,
        stakes=tuple(stakes),
        payouts=tuple(payouts),
        profit=min(payouts) - staked,
    )
