"""Regenerate vectors.json - the shared test vectors used by both packages.

Expected values are computed here *independently* of the Python and
JavaScript implementations: exact rational arithmetic (fractions.Fraction)
for closed-form results and 50-digit mpmath root finding for the power and
Shin methods. Never fill in an expected value by running odds_tools itself.

    pip install mpmath
    python test-vectors/generate.py

Each case is {"fn", "args", "expected"} or {"fn", "args", "error": true}.
Function names are the Python (snake_case) names; the JavaScript suite maps
them to camelCase, and maps snake_case keys of expected objects the same way.
Non-JSON numbers are written as {"$number": "NaN" | "Infinity" | "-Infinity"}.
Numbers are compared with |actual - expected| <= 1e-9 * max(1, |expected|).
"""

from __future__ import annotations

import json
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction as F
from itertools import combinations
from math import comb
from pathlib import Path

from mpmath import findroot, mp, mpf, sqrt

mp.dps = 50

NAN = {"$number": "NaN"}
INF = {"$number": "Infinity"}

cases: list[dict] = []


def ok(fn, args, expected, note=None):
    case = {"fn": fn, "args": args, "expected": expected}
    if note:
        case["note"] = note
    cases.append(case)


def err(fn, args, note=None):
    case = {"fn": fn, "args": args, "error": True}
    if note:
        case["note"] = note
    cases.append(case)


def q(x) -> F:
    """Exact rational value of a price as written."""
    return F(repr(x)) if isinstance(x, float) else F(x)


def fl(x) -> float:
    return float(x)


# --- conversions ---------------------------------------------------------------

for d, frac in [
    (3.5, "5/2"), (2.0, "1/1"), (1.5, "1/2"), (1.91, "91/100"), (1.8, "4/5"),
    (11.0, "10/1"), (2.375, "11/8"), (7.5, "13/2"), (1.4, "2/5"), (1.01, "1/100"),
]:
    ok("decimal_to_fractional", [d], frac)
ok("decimal_to_fractional", [1.909], "10/11", "closest fraction with denominator <= 100")
ok("decimal_to_fractional", [1.333], "1/3", "closest fraction with denominator <= 100")
ok("decimal_to_fractional", [1.909, 10], "9/10", "max_denominator = 10")
ok("decimal_to_fractional", [1.001, 1000], "1/1000")
err("decimal_to_fractional", [1.001], "closest fraction with denominator <= 100 is 0/1")
err("decimal_to_fractional", [2.5, 0], "max_denominator must be >= 1")
for bad in [1.0, 0.5, -2.0, 0, "2.5", None, True, NAN, INF]:
    err("decimal_to_fractional", [bad])

for frac, d in [
    ("5/2", F(7, 2)), ("1/1", 2), ("evens", 2), (" EVS ", 2), ("11/8", F(19, 8)),
    ("100/30", F(13, 3)), ("1/100", F(101, 100)), (" 10 / 11 ", F(21, 11)),
]:
    ok("fractional_to_decimal", [frac], fl(d))
for bad in ["0/1", "5/0", "5-2", "2.5/1", "-5/2", "", "abc", 2.5, None]:
    err("fractional_to_decimal", [bad])


def american(d: F) -> F:
    return (d - 1) * 100 if d >= 2 else F(-100) / (d - 1)


for d in [2.5, 1.5, 2.0, 1.91, 11.0, 1.01, 1.952]:
    ok("decimal_to_american", [d], fl(american(q(d))))
for bad in [1.0, 0, -150, "2.5", NAN]:
    err("decimal_to_american", [bad])

for a, d in [(150, F(5, 2)), (-200, F(3, 2)), (100, 2), (-100, 2), (-110, F(21, 11)),
             (1000, 11), (-10000, F(101, 100)), (137.5, F(1375, 1000) + 1)]:
    ok("american_to_decimal", [a], fl(d))
for bad in [50, -99.9, 0, 99.99, "+150", INF]:
    err("american_to_decimal", [bad])

ok("format_american", [150], "+150")
ok("format_american", [-200], "-200")
ok("format_american", [100], "+100")
ok("format_american", [-109.89010989010988], "-110")
ok("format_american", [-109.89010989010988, 2], "-109.89")
ok("format_american", [100.5], "+101", "half rounds away from zero")
ok("format_american", [-237.5], "-238", "half rounds away from zero")
err("format_american", [99])
err("format_american", [150, -1])

for d in [2.5, 1.8, 1.05, 10.0]:
    hk = q(d) - 1
    ok("decimal_to_hongkong", [d], fl(hk))
    ok("decimal_to_indonesian", [d], fl(hk if q(d) >= 2 else F(-1) / hk))
    ok("decimal_to_malay", [d], fl(hk if q(d) <= 2 else F(-1) / hk))
ok("decimal_to_indonesian", [2.0], 1.0)
ok("decimal_to_malay", [2.0], 1.0)
for fn in ["decimal_to_hongkong", "decimal_to_indonesian", "decimal_to_malay"]:
    err(fn, [1.0])

ok("hongkong_to_decimal", [0.8], 1.8)
ok("hongkong_to_decimal", [1.5], 2.5)
for bad in [0, -0.5, "0.8"]:
    err("hongkong_to_decimal", [bad])

for i, d in [(-2, F(3, 2)), (1.5, F(5, 2)), (-1, 2), (1, 2), (-1.25, F(9, 5))]:
    ok("indonesian_to_decimal", [i], fl(d))
for bad in [0.5, -0.5, 0]:
    err("indonesian_to_decimal", [bad])

for m, d in [(0.5, F(3, 2)), (-0.5, 3), (-1, 2), (1, 2), (0.8, F(9, 5)), (-0.25, 5)]:
    ok("malay_to_decimal", [m], fl(d))
for bad in [1.5, 0, -1.5]:
    err("malay_to_decimal", [bad])

ok("implied_probability", [2.5], 0.4)
ok("implied_probability", [4.0], 0.25)
ok("implied_probability", [1.91], fl(1 / q(1.91)))
err("implied_probability", [1.0], "odds of 1 or less are invalid")
err("implied_probability", [0], "zero odds")

ok("probability_to_decimal", [0.4], 2.5)
ok("probability_to_decimal", [0.8], 1.25)
for bad in [0, 1, 1.2, -0.1]:
    err("probability_to_decimal", [bad], "probability must be strictly between 0 and 1")

ok("convert", ["3/2", "fractional", "american"], 150.0)
ok("convert", [-110, "american", "fractional"], "10/11")
ok("convert", [0.25, "probability", "fractional"], "3/1")
ok("convert", [1.5, "hongkong", "malay"], fl(F(-2, 3)))
ok("convert", [-2, "indonesian", "decimal"], 1.5)
ok("convert", [2.5, "decimal", "probability"], 0.4)
ok("convert", ["5/2", "fractional", "fractional"], "5/2")
ok("convert", [-0.5, "malay", "american"], 200.0)
ok("convert", [0.8, "hongkong", "american"], -125.0)
err("convert", [2.5, "decimal", "roman"])
err("convert", [2.5, "roman", "decimal"])
err("convert", ["5/2", "decimal", "american"], "a string is not a decimal price")
ok("to_decimal", [-125, "american"], 1.8)
ok("from_decimal", [1.8, "american"], -125.0)
ok("from_decimal", [1.8, "fractional"], "4/5")


# --- rounding ----------------------------------------------------------------------


def half_up(x: float, places: int) -> float:
    return float(Decimal(repr(x)).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))


for x, n in [(2.675, 2), (1.005, 2), (2.5, 0), (-2.5, 0), (-0.125, 2), (1.2345, 3),
             (1.91, 2), (123.456, 1), (0.000001, 6), (1.5e-7, 7), (1e21, 2), (7.0, 2)]:
    ok("round_half_up", [x, n], half_up(x, n))
ok("round_half_up", [2.675], 2.68, "default is 2 decimals")
for args in [[2.5, -1], [2.5, 1.5], [2.5, 16], ["2.5", 2], [NAN, 2]]:
    err("round_half_up", args)


# --- margin and fair odds ------------------------------------------------------------

MARKETS = {
    "football_1x2": [1.525, 5.08, 6.15],
    "even_two_way": [1.9, 1.9],
    "tennis_two_way": [1.25, 3.9],
    "four_way_longshots": [1.2, 6.5, 15.0, 26.0],
}

for name, odds in MARKETS.items():
    implied = [1 / q(d) for d in odds]
    book = sum(implied)
    ok("overround", [odds], fl(book), name)
    ok("margin", [odds], fl(book - 1), name)
    ok("market_payout", [odds], fl(1 / book), name)
    ok("implied_probabilities", [odds], [fl(p) for p in implied], name)

ok("implied_probabilities", [[2.0]], [0.5])
ok("margin", [[2.1, 2.05]], fl(1 / q(2.1) + 1 / q(2.05) - 1), "negative margin: arbitrage")
err("overround", [[2.0]], "a market needs at least two outcomes")
err("overround", [[]])
err("overround", [[2.0, 1.0]])
err("margin", [[2.0, 0]])
err("margin", ["1.9,1.9"])


def devig(odds, method):
    pi = [mpf(1) / mpf(repr(d)) for d in odds]
    s = sum(pi)
    n = len(pi)
    if method == "multiplicative":
        return [p / s for p in pi]
    if method == "additive":
        return [p - (s - 1) / n for p in pi]
    if method == "power":
        k = findroot(lambda k: sum(p**k for p in pi) - 1, mpf(1))
        return [p**k for p in pi]
    if method == "shin":
        def probs(z):
            return [(sqrt(z * z + 4 * (1 - z) * p * p / s) - z) / (2 * (1 - z)) for p in pi]

        z = findroot(lambda z: sum(probs(z)) - 1, mpf("0.01"))
        return probs(z)
    raise ValueError(method)


for name, odds in MARKETS.items():
    for method in ["multiplicative", "additive", "power", "shin"]:
        probs = devig(odds, method)
        assert abs(sum(probs) - 1) < mpf("1e-40"), (name, method)
        ok("fair_probabilities", [odds, method], [fl(p) for p in probs], name)
        ok("fair_odds", [odds, method], [fl(1 / p) for p in probs], name)
ok("fair_probabilities", [[1.525, 5.08, 6.15]],
   [fl(p) for p in devig([1.525, 5.08, 6.15], "multiplicative")], "default method")
ok("fair_probabilities", [[2.2, 2.0], "additive"],
   [fl(p) for p in devig([2.2, 2.0], "additive")], "arbitrage market")
ok("fair_probabilities", [[2.2, 2.0], "power"],
   [fl(p) for p in devig([2.2, 2.0], "power")], "arbitrage market")
ok("fair_probabilities", [[2.0, 2.0], "shin"], [0.5, 0.5], "no margin: z = 0")
err("fair_probabilities", [[2.2, 2.0], "shin"], "Shin needs a positive margin")
err("fair_probabilities", [[1.1, 8.0, 101.0], "additive"],
    "margin share exceeds the long shot's implied probability")
err("fair_probabilities", [[1.9, 1.9], "logarithmic"])
err("fair_probabilities", [[1.9], "multiplicative"])
err("fair_odds", [[1.9, 0.9]])

for name, odds in MARKETS.items():
    pi = [mpf(1) / mpf(repr(d)) for d in odds]
    s = sum(pi)
    z = findroot(
        lambda z: sum((sqrt(z * z + 4 * (1 - z) * p * p / s) - z) / (2 * (1 - z)) for p in pi) - 1,
        mpf("0.01"),
    )
    ok("shin_z", [odds], fl(z), name)
ok("shin_z", [[2.0, 2.0]], 0.0)
err("shin_z", [[2.2, 2.0]])


# --- accumulators and system bets -------------------------------------------------------


def prod(values):
    result = F(1)
    for v in values:
        result *= v
    return result


ok("accumulator_odds", [[1.5, 2.0, 3.0]], 9.0)
ok("accumulator_odds", [[2.0]], 2.0)
ok("accumulator_odds", [[1.91, 1.83, 2.05, 1.72]], fl(prod(q(d) for d in [1.91, 1.83, 2.05, 1.72])))
err("accumulator_odds", [[]])
err("accumulator_odds", [[1.5, 0.9]])

ok("accumulator_payout", [10, [1.5, 2.0, 3.0]], 90.0)
ok("accumulator_payout", [10, [1.5, 2.0, 3.0], ["win", "void", "win"]], 45.0)
ok("accumulator_payout", [10, [1.5, 2.0, 3.0], ["win", "lose", "win"]], 0.0)
ok("accumulator_payout", [10, [1.5, 2.0, 3.0], [True, True, True]], 90.0)
ok("accumulator_payout", [10, [1.5, 2.0], ["void", "void"]], 10.0, "all legs void: stake back")
ok("accumulator_payout", [0, [1.5, 2.0]], 0.0)
err("accumulator_payout", [10, [1.5, 2.0], ["win"]])
err("accumulator_payout", [10, [1.5, 2.0], ["win", "draw"]])
err("accumulator_payout", [10, [1.5, 2.0], ["win", 1]])
err("accumulator_payout", [-10, [1.5, 2.0]])

ok("system_combinations", [3, 2], [[0, 1], [0, 2], [1, 2]])
ok("system_combinations", [4, [3, 2]], [list(c) for k in (2, 3) for c in combinations(range(4), k)])
ok("system_combinations", [3, [1, 1]], [[0], [1], [2]], "duplicate sizes are merged")
err("system_combinations", [3, 4])
err("system_combinations", [0, 1])
err("system_combinations", [3, []])


def system(odds, sizes, stake, results=None):
    sizes = sorted({sizes} if isinstance(sizes, int) else set(sizes))
    n = len(odds)
    bets = sum(comb(n, k) for k in sizes)
    unit = F(repr(float(stake))) / bets
    factors = [q(d) for d in odds]
    if results is not None:
        factors = [
            q(d) if r in ("win", True) else (F(0) if r in ("lose", False) else F(1))
            for d, r in zip(odds, results)
        ]
    total = sum(prod(factors[i] for i in c) for k in sizes for c in combinations(range(n), k))
    return {
        "legs": n,
        "sizes": sizes,
        "bets": bets,
        "unit_stake": fl(unit),
        "total_stake": float(stake),
        "max_payout": fl(unit * total),
    }, fl(unit * total)


for args, note in [
    ([[2.0, 3.0, 4.0], 2, 30], "2/3 system"),
    ([[1.5, 2.0, 2.5, 3.0], 3, 40], "3/4 system"),
    ([[2.0, 2.0, 2.0, 2.0], [2, 3, 4], 11], "Yankee: 11 bets"),
    ([[1.8, 2.1, 2.4, 1.95], [1, 2, 3, 4], 15], "Lucky 15"),
    ([[1.8, 2.1, 2.4], [2, 3], 8], "Trixie: 4 bets"),
]:
    ok("system_bet", args, system(*args)[0], note)
err("system_bet", [[2.0, 3.0], 3, 10])
err("system_bet", [[2.0, 3.0, 4.0], 2, -1])

for args, note in [
    ([[2.0, 3.0, 4.0], 2, 30, ["win", "win", "lose"]], "one leg lost"),
    ([[2.0, 3.0, 4.0], 2, 30, ["win", "void", "win"]], "void leg counts as 1.0"),
    ([[2.0, 3.0, 4.0], 2, 30, ["void", "void", "void"]], "all void: stakes back"),
    ([[2.0, 3.0, 4.0], 2, 30, ["lose", "lose", "win"]], "two legs lost"),
    ([[1.5, 2.0, 2.5, 3.0], 3, 40, ["win", "win", "lose", "win"]], "3/4, one leg lost"),
    ([[1.5, 2.0, 2.5, 3.0], 3, 40, [True, True, True, True]], "3/4, all won"),
    ([[1.8, 2.1, 2.4, 1.95], [1, 2, 3, 4], 15, ["win", "lose", "void", "win"]], "Lucky 15"),
]:
    ok("system_payout", args, system(*args)[1], note)
err("system_payout", [[2.0, 3.0, 4.0], 2, 30, ["win", "win"]])
err("system_payout", [[2.0, 3.0, 4.0], 2, 30, "win,win,win"])


# --- expected value and Kelly -----------------------------------------------------------

ok("expected_value", [2.1, 0.5], fl(q(2.1) * q(0.5) - 1))
ok("expected_value", [2.1, 0.5, 100], fl(100 * (q(2.1) * q(0.5) - 1)))
ok("expected_value", [1.8, 0.5, 10], fl(10 * (q(1.8) * q(0.5) - 1)))
ok("expected_value", [3.0, 0.0, 10], -10.0)
err("expected_value", [2.0, 1.2])
err("expected_value", [2.0, 0.5, -1])
err("expected_value", [1.0, 0.5])


def kelly(d, p, fraction=1):
    d, p = q(d), q(p)
    full = (p * d - 1) / (d - 1)
    return fl(max(F(0), full) * q(fraction))


for args in [[2.0, 0.55], [2.0, 0.55, 0.5], [3.0, 0.4], [2.0, 0.45], [1.5, 1.0],
             [2.5, 0.5, 0.25], [1.91, 0.5]]:
    ok("kelly_fraction", args, kelly(*args))
for args in [[2.0, 0.55, 0], [2.0, 0.55, 1.5], [2.0, -0.1], [0.5, 0.5]]:
    err("kelly_fraction", args)
ok("kelly_stake", [1000, 3.0, 0.4, 0.25], 1000 * kelly(3.0, 0.4, 0.25))
ok("kelly_stake", [1000, 2.0, 0.45], 0.0, "no edge: no bet")
err("kelly_stake", [-1, 2.0, 0.55])


# --- arbitrage --------------------------------------------------------------------------

ok("is_arbitrage", [[2.1, 2.05]], True)
ok("is_arbitrage", [[1.9, 1.9]], False)
ok("is_arbitrage", [[2.6, 3.9, 3.7]], True)
ok("is_arbitrage", [[2.0, 2.0]], False, "overround exactly 1 is not an arbitrage")
err("is_arbitrage", [[2.1]])


def arb(odds, total, decimals=None):
    pi = [1 / q(d) for d in odds]
    book = sum(pi)
    stakes = [q(total) * p / book for p in pi]
    if decimals is not None:
        stakes = [q(half_up(float(s), decimals)) for s in stakes]
    payouts = [s * q(d) for s, d in zip(stakes, odds)]
    staked = sum(stakes)
    return {
        "is_arbitrage": book < 1,
        "overround": fl(book),
        "profit_margin": fl(1 / book - 1),
        "total_stake": fl(staked),
        "stakes": [fl(s) for s in stakes],
        "payouts": [fl(p) for p in payouts],
        "profit": fl(min(payouts) - staked),
    }


for args, note in [
    ([[2.1, 2.05], 100], "2-way surebet"),
    ([[2.1, 2.05], 100, 2], "stakes rounded to cents"),
    ([[2.6, 3.9, 3.7], 1000], "3-way surebet"),
    ([[2.6, 3.9, 3.7], 1000, 0], "stakes rounded to whole units"),
    ([[1.9, 1.9], 100], "not an arbitrage: negative profit"),
]:
    ok("arbitrage", args, arb(*args), note)
err("arbitrage", [[2.1, 2.05], 0])
err("arbitrage", [[2.1], 100])
err("arbitrage", [[2.1, 2.05], 100, -1])


header = {
    "description": "Shared test vectors for odds-tools (Python and JavaScript). "
    "Generated by test-vectors/generate.py; do not edit by hand.",
    "tolerance": 1e-9,
}
# One case per line keeps the file readable and diffs small.
body = ",\n".join("  " + json.dumps(case, ensure_ascii=False) for case in cases)
text = json.dumps(header, indent=1)[:-2] + ',\n "cases": [\n' + body + "\n ]\n}\n"
json.loads(text)  # sanity check
path = Path(__file__).with_name("vectors.json")
path.write_text(text, encoding="utf-8")
print(f"wrote {len(cases)} cases to {path}")
