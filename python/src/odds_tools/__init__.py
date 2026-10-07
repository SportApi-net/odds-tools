"""Dependency-free betting-odds math: conversions, margin, fair odds,
accumulators, system bets, Kelly staking, expected value and arbitrage.

All prices are decimal odds unless a function name says otherwise. Invalid
input raises :class:`OddsError` (a :class:`ValueError` subclass).
"""

from ._validate import OddsError
from .arbitrage import Arbitrage, arbitrage, is_arbitrage
from .bets import (
    RESULTS,
    SystemBet,
    accumulator_odds,
    accumulator_payout,
    system_bet,
    system_combinations,
    system_payout,
)
from .convert import (
    FORMATS,
    american_to_decimal,
    convert,
    decimal_to_american,
    decimal_to_fractional,
    decimal_to_hongkong,
    decimal_to_indonesian,
    decimal_to_malay,
    format_american,
    fractional_to_decimal,
    from_decimal,
    hongkong_to_decimal,
    implied_probability,
    indonesian_to_decimal,
    malay_to_decimal,
    probability_to_decimal,
    to_decimal,
)
from .margin import (
    METHODS,
    fair_odds,
    fair_probabilities,
    implied_probabilities,
    margin,
    market_payout,
    overround,
    shin_z,
)
from .rounding import round_half_up
from .staking import expected_value, kelly_fraction, kelly_stake

__version__ = "0.1.1"

__all__ = [
    "FORMATS",
    "METHODS",
    "RESULTS",
    "Arbitrage",
    "OddsError",
    "SystemBet",
    "accumulator_odds",
    "accumulator_payout",
    "american_to_decimal",
    "arbitrage",
    "convert",
    "decimal_to_american",
    "decimal_to_fractional",
    "decimal_to_hongkong",
    "decimal_to_indonesian",
    "decimal_to_malay",
    "expected_value",
    "fair_odds",
    "fair_probabilities",
    "format_american",
    "fractional_to_decimal",
    "from_decimal",
    "hongkong_to_decimal",
    "implied_probabilities",
    "implied_probability",
    "indonesian_to_decimal",
    "is_arbitrage",
    "kelly_fraction",
    "kelly_stake",
    "malay_to_decimal",
    "margin",
    "market_payout",
    "overround",
    "probability_to_decimal",
    "round_half_up",
    "shin_z",
    "system_bet",
    "system_combinations",
    "system_payout",
    "to_decimal",
]
