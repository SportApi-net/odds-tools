"""Behaviour and property tests that complement the shared vectors."""

from __future__ import annotations

import itertools
import math
import random
from fractions import Fraction

import pytest

import odds_tools as ot
from odds_tools import OddsError


def test_odds_error_is_value_error() -> None:
    assert issubclass(OddsError, ValueError)
    with pytest.raises(ValueError, match="greater than 1"):
        ot.implied_probability(1.0)


@pytest.mark.parametrize("bad", [True, "2.0", None, math.nan, math.inf, [2.0]])
def test_decimal_odds_type_validation(bad: object) -> None:
    with pytest.raises(OddsError):
        ot.decimal_to_american(bad)  # type: ignore[arg-type]


def test_fraction_and_int_inputs_are_accepted() -> None:
    assert ot.decimal_to_american(Fraction(5, 2)) == 150.0  # type: ignore[arg-type]
    assert ot.american_to_decimal(-200) == 1.5


@pytest.mark.parametrize("fmt", [f for f in ot.FORMATS if f != "fractional"])
def test_numeric_round_trips(fmt: str) -> None:
    rng = random.Random(7)
    for _ in range(500):
        d = 1 + rng.uniform(0.001, 50)
        assert ot.to_decimal(ot.from_decimal(d, fmt), fmt) == pytest.approx(d, rel=1e-12)


def test_fractional_round_trip_for_ladder_prices() -> None:
    for numerator, denominator in itertools.product(range(1, 41), range(1, 21)):
        frac = Fraction(numerator, denominator)
        text = f"{frac.numerator}/{frac.denominator}"
        assert ot.decimal_to_fractional(ot.fractional_to_decimal(text)) == text


def test_american_and_indonesian_agree() -> None:
    for d in [1.01, 1.5, 1.91, 2.0, 2.5, 13.0]:
        assert ot.decimal_to_indonesian(d) == pytest.approx(ot.decimal_to_american(d) / 100)


def test_malay_is_inverse_of_indonesian() -> None:
    for d in [1.2, 1.5, 3.0, 7.5]:
        assert ot.decimal_to_malay(d) == pytest.approx(-1 / ot.decimal_to_indonesian(d))


@pytest.mark.parametrize("method", ot.METHODS)
def test_fair_probabilities_sum_to_one(method: str) -> None:
    rng = random.Random(11)
    for _ in range(200):
        n = rng.randint(2, 6)
        true = [rng.uniform(0.05, 1) for _ in range(n)]
        total = sum(true)
        book = 1 + rng.uniform(0.01, 0.12)
        odds = [1 / (p / total * book) for p in true]
        if any(d <= 1 for d in odds):
            continue
        try:
            probs = ot.fair_probabilities(odds, method)
        except OddsError:
            assert method == "additive"
            continue
        assert math.fsum(probs) == pytest.approx(1, abs=1e-12)
        assert all(0 < p < 1 for p in probs)
        # With a positive margin every fair price is longer than the quoted one.
        assert all(f > d for f, d in zip(ot.fair_odds(odds, method), odds))


def test_shin_equals_additive_for_two_outcomes() -> None:
    # With two outcomes Shin's model gives the same probabilities as the
    # additive method; checked numerically here.
    for odds in ([1.8, 2.0], [1.25, 3.9], [1.05, 9.0]):
        assert ot.fair_probabilities(odds, "shin") == pytest.approx(
            ot.fair_probabilities(odds, "additive"), abs=1e-12
        )


def test_shin_and_power_shrink_longshots_more_than_multiplicative() -> None:
    odds = [1.2, 6.5, 15.0, 26.0]
    mult = ot.fair_probabilities(odds)
    for method in ("power", "shin"):
        probs = ot.fair_probabilities(odds, method)
        assert probs[0] > mult[0]
        assert probs[-1] < mult[-1]


def test_no_margin_market_is_unchanged() -> None:
    for method in ot.METHODS:
        assert ot.fair_probabilities([2.0, 4.0, 4.0], method) == pytest.approx([0.5, 0.25, 0.25])
    assert ot.shin_z([2.0, 4.0, 4.0]) == pytest.approx(0, abs=1e-12)


def test_system_payout_matches_brute_force() -> None:
    rng = random.Random(3)
    for _ in range(100):
        n = rng.randint(2, 7)
        odds = [round(rng.uniform(1.1, 5), 2) for _ in range(n)]
        sizes = sorted(rng.sample(range(1, n + 1), rng.randint(1, n)))
        results = [rng.choice(["win", "lose", "void"]) for _ in range(n)]
        bet = ot.system_bet(odds, sizes, 100)
        combos = ot.system_combinations(n, sizes)
        assert len(combos) == bet.bets
        factor = {"win": None, "lose": 0.0, "void": 1.0}
        brute = 0.0
        for combo in combos:
            value = bet.unit_stake
            for i in combo:
                f = factor[results[i]]
                value *= odds[i] if f is None else f
            brute += value
        assert ot.system_payout(odds, sizes, 100, results) == pytest.approx(brute)
        all_win = ot.system_payout(odds, sizes, 100, ["win"] * n)
        assert all_win == pytest.approx(bet.max_payout)


def test_full_size_system_is_an_accumulator() -> None:
    odds = [1.5, 2.2, 1.8]
    assert ot.system_bet(odds, 3, 10).max_payout == pytest.approx(ot.accumulator_payout(10, odds))


def test_system_bet_result_is_frozen() -> None:
    bet = ot.system_bet([2.0, 3.0, 4.0], 2, 30)
    with pytest.raises(AttributeError):
        bet.bets = 4  # type: ignore[misc]


def test_arbitrage_payouts_are_equal_without_rounding() -> None:
    result = ot.arbitrage([2.6, 3.9, 3.7], 1000)
    assert result.is_arbitrage
    assert max(result.payouts) - min(result.payouts) < 1e-9
    assert result.profit == pytest.approx(1000 * result.profit_margin)
    assert sum(result.stakes) == pytest.approx(1000)


def test_kelly_growth_is_maximal_at_full_kelly() -> None:
    d, p = 2.2, 0.5
    f = ot.kelly_fraction(d, p)

    def growth(x: float) -> float:
        return p * math.log(1 + x * (d - 1)) + (1 - p) * math.log(1 - x)

    assert growth(f) > growth(f * 0.9)
    assert growth(f) > growth(f * 1.1)


def test_expected_value_sign_matches_kelly() -> None:
    for d, p in [(2.0, 0.55), (2.0, 0.45), (3.4, 0.3), (1.5, 0.7)]:
        assert (ot.expected_value(d, p) > 0) == (ot.kelly_fraction(d, p) > 0)


def test_round_half_up_differs_from_builtin_round() -> None:
    assert round(2.675, 2) == 2.67
    assert ot.round_half_up(2.675, 2) == 2.68
    assert round(0.5) == 0
    assert ot.round_half_up(0.5, 0) == 1.0


def test_version() -> None:
    assert ot.__version__ == "0.1.0"


def test_convert_return_types() -> None:
    fractional: str = ot.convert(2.5, "decimal", "fractional")
    american: float = ot.convert("3/2", "fractional", "american")
    assert (fractional, american) == ("3/2", 150.0)
