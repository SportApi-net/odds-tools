# odds-tools

Betting-odds math for **Python** and **JavaScript/TypeScript**: format conversion, bookmaker margin, no-vig fair odds, accumulators, system bets, Kelly staking, expected value and arbitrage. Zero dependencies, the same API in both languages, and one shared set of test vectors that keeps the two implementations in agreement.

[![PyPI](https://img.shields.io/pypi/v/odds-tools.svg)](https://pypi.org/project/odds-tools/)
[![npm](https://img.shields.io/npm/v/odds-tools.svg)](https://www.npmjs.com/package/odds-tools)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-3776ab.svg)](python/)
[![TypeScript](https://img.shields.io/badge/TypeScript-ESM%20%2B%20CJS-3178c6.svg)](js/)
[![Zero dependencies](https://img.shields.io/badge/dependencies-0-brightgreen.svg)](#)
[![CI](https://github.com/SportApi-net/odds-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/SportApi-net/odds-tools/actions/workflows/ci.yml)

## Features

- **Conversions** between decimal, fractional (`"5/2"`), American (`+150` / `-200`), Hong Kong, Indonesian and Malay odds, plus implied probability.
- **Margin**: overround, bookmaker margin and theoretical payout of a market.
- **Fair (no-vig) odds** with four methods: multiplicative, additive, power and Shin.
- **Accumulators (parlays)** with win / lose / void legs.
- **System bets**: 2/3, 3/4, Trixie, Yankee, Lucky 15 and any other combination of sizes, with stake split and payout for a given set of results.
- **Kelly criterion** (full and fractional) and **expected value**.
- **Arbitrage (surebet)** detection and stake distribution for 2-way, 3-way and larger markets, with optional stake rounding.
- **Predictable rounding** (`round_half_up(2.675) == 2.68`) and **strict validation**: every bad input raises one error type with a clear message.
- Typed: `py.typed` for Python, bundled `.d.ts` for both the ESM and the CommonJS build.

## Install

```bash
pip install odds-tools      # Python 3.9+
npm install odds-tools      # Node 18+ or any ES2020 bundler
```

## Quick start

**Python**

```python
from odds_tools import convert, margin, fair_odds, kelly_stake, arbitrage

convert("5/2", "fractional", "american")     # 250.0
convert(-110, "american", "fractional")      # '10/11'

prices = [1.36, 5.35, 9.4]                   # 1X2 market: home, draw, away
margin(prices)                               # 0.0286  -> 2.86 % bookmaker margin
fair_odds(prices)                            # [1.399, 5.503, 9.669]
fair_odds(prices, "shin")                    # [1.383, 5.604, 10.146]

kelly_stake(1000, odds=2.2, probability=0.5, fraction=0.5)   # 41.67 (half Kelly)

arb = arbitrage([2.1, 2.05], total_stake=100, decimals=2)
arb.stakes, arb.profit                       # (49.4, 50.6), 3.73
```

**TypeScript / JavaScript**

```ts
import { convert, margin, fairOdds, kellyStake, arbitrage } from 'odds-tools';

convert('5/2', 'fractional', 'american');    // 250
convert(-110, 'american', 'fractional');     // '10/11'

const prices = [1.36, 5.35, 9.4];
margin(prices);                              // 0.0286
fairOdds(prices);                            // [1.399, 5.503, 9.669]
fairOdds(prices, 'shin');                    // [1.383, 5.604, 10.146]

kellyStake(1000, 2.2, 0.5, 0.5);             // 41.67

const arb = arbitrage([2.1, 2.05], 100, 2);
console.log(arb.stakes, arb.profit);         // [49.4, 50.6] 3.73
```

CommonJS works too: `const { convert } = require('odds-tools');`.

Outputs in comments are rounded for readability; functions return full-precision floats. Use `round_half_up` / `roundHalfUp` for display.

## Usage

Python uses `snake_case`, JavaScript uses `camelCase`; arguments are the same and in the same order. The examples below are Python.

### Odds formats

Decimal odds are the hub: every converter goes through them. `convert(value, from, to)` accepts any pair of formats from `FORMATS`.

| Format | Example (decimal 2.5) | Example (decimal 1.8) | From decimal `d` | Valid values |
|---|---|---|---|---|
| `decimal` | `2.5` | `1.8` | `d` | `> 1` |
| `fractional` | `"3/2"` | `"4/5"` | `d − 1` as a reduced fraction | `"n/m"`, `n, m > 0`; `"evens"` |
| `american` | `+150` | `−125` | `(d−1)·100` if `d ≥ 2`, else `−100/(d−1)` | `≥ +100` or `≤ −100` |
| `hongkong` | `1.5` | `0.8` | `d − 1` | `> 0` |
| `indonesian` | `1.5` | `−1.25` | `d − 1` if `d ≥ 2`, else `−1/(d−1)` | `≥ 1` or `≤ −1` |
| `malay` | `−0.667` | `0.8` | `d − 1` if `d ≤ 2`, else `−1/(d−1)` | `(0, 1]` or `[−1, 0)` |
| `probability` | `0.4` | `0.556` | `1/d` | `(0, 1)` |

```python
from odds_tools import (decimal_to_fractional, fractional_to_decimal, decimal_to_american,
                        american_to_decimal, format_american, implied_probability)

fractional_to_decimal("11/8")                 # 2.375
decimal_to_fractional(1.909)                  # '10/11'  closest fraction, denominator <= 100
decimal_to_fractional(1.909, max_denominator=10)  # '9/10'
american_to_decimal(-200)                     # 1.5
format_american(decimal_to_american(1.91))    # '-110'
implied_probability(1.8)                      # 0.5556
```

### Margin and fair (no-vig) odds

`odds` is the list of decimal prices of **one** market whose outcomes are mutually exclusive and exhaustive (1X2, both sides of a total, all runners of a race).

```python
from odds_tools import overround, margin, market_payout, fair_probabilities, fair_odds, shin_z

prices = [1.36, 5.35, 9.4]
overround(prices)        # 1.0286   sum of 1/d
margin(prices)           # 0.0286   overround - 1
market_payout(prices)    # 0.9722   1 / overround ("return to player")

for method in ("multiplicative", "additive", "power", "shin"):
    print(method, fair_odds(prices, method))
# multiplicative [1.399, 5.503, 9.669]
# additive       [1.378, 5.637, 10.325]
# power          [1.376, 5.700, 10.230]
# shin           [1.383, 5.604, 10.146]
```

| Method | Fair probability | Notes |
|---|---|---|
| `multiplicative` (default) | `pᵢ = πᵢ / S` | Margin spread in proportion to each price. Simple and the most common. |
| `additive` | `pᵢ = πᵢ − (S − 1)/n` | Equal margin on every outcome. Raises `OddsError` if a long shot would get `p ≤ 0`. |
| `power` | `pᵢ = πᵢᵏ`, `k` such that `Σ pᵢ = 1` | Takes more margin from long shots. Works for any overround. |
| `shin` | Shin (1993), solved for `z` | Models insider trading; corrects the favourite–longshot bias. Needs `S ≥ 1`. `shin_z(prices)` returns `z`. |

where `πᵢ = 1/dᵢ` and `S = Σ πᵢ` (the overround). With two outcomes, Shin and additive give the same result.

### Accumulators (parlays)

```python
from odds_tools import accumulator_odds, accumulator_payout

accumulator_odds([1.91, 1.83, 2.05])                              # 7.165
accumulator_payout(10, [1.91, 1.83, 2.05])                        # 71.65
accumulator_payout(10, [1.91, 1.83, 2.05], ["win", "void", "win"])  # 39.155 (void leg = 1.0)
accumulator_payout(10, [1.91, 1.83, 2.05], ["win", "lose", "win"])  # 0.0
```

Results per leg are `"win"`, `"lose"`, `"void"` (or `True` / `False`).

### System bets

`sizes` is the accumulator size (`2` for a "2 from 3" system) or a list of sizes for full-cover bets. The total stake is split equally across all combinations.

```python
from odds_tools import system_bet, system_payout, system_combinations

bet = system_bet([1.9, 2.1, 2.4], sizes=2, total_stake=30)
# SystemBet(legs=3, sizes=(2,), bets=3, unit_stake=10.0, total_stake=30.0, max_payout=135.9)

system_payout([1.9, 2.1, 2.4], 2, 30, ["win", "win", "lose"])   # 39.9 (only 1.9 x 2.1 wins)
system_combinations(3, 2)                                       # [(0, 1), (0, 2), (1, 2)]

system_bet([1.8, 2.0, 2.2, 2.5], [2, 3, 4], 22).bets            # 11 - a Yankee
```

| Name | Legs | `sizes` | Bets |
|---|---|---|---|
| 2/3 | 3 | `2` | 3 |
| 3/4 | 4 | `3` | 4 |
| Trixie | 3 | `[2, 3]` | 4 |
| Patent | 3 | `[1, 2, 3]` | 7 |
| Yankee | 4 | `[2, 3, 4]` | 11 |
| Lucky 15 | 4 | `[1, 2, 3, 4]` | 15 |
| Super Yankee (Canadian) | 5 | `[2, 3, 4, 5]` | 26 |
| Heinz | 6 | `[2, 3, 4, 5, 6]` | 57 |

Payouts are computed without enumerating combinations (the sum of products over all `k`-leg subsets is the elementary symmetric polynomial `eₖ`), so large systems are cheap.

### Expected value and Kelly criterion

```python
from odds_tools import expected_value, kelly_fraction, kelly_stake

expected_value(2.2, probability=0.5)             # 0.10   +10 % per unit staked
expected_value(2.2, probability=0.5, stake=100)  # 10.0
kelly_fraction(2.2, probability=0.5)             # 0.0833 of the bankroll (full Kelly)
kelly_stake(1000, 2.2, 0.5, fraction=0.5)        # 41.67  (half Kelly)
kelly_fraction(1.8, probability=0.5)             # 0.0    no edge -> no bet
```

### Arbitrage (surebets)

```python
from odds_tools import is_arbitrage, arbitrage

is_arbitrage([2.1, 2.05])                 # True  (1/2.1 + 1/2.05 = 0.964 < 1)

arbitrage([2.6, 3.9, 3.7], total_stake=1000, decimals=0)
# Arbitrage(is_arbitrage=True, overround=0.9113, profit_margin=0.0973,
#           total_stake=1000.0, stakes=(422.0, 281.0, 297.0),
#           payouts=(1097.2, 1095.9, 1098.9), profit=95.9)
```

Stakes are proportional to `1/dᵢ`, so every outcome returns `total / S`. With `decimals` the stakes are rounded half-up and `payouts` / `profit` are recomputed from the rounded stakes (`profit` is the guaranteed minimum). Non-arbitrage markets are accepted too — the profit is then negative, which is useful for hedging.

### Rounding

```python
from odds_tools import round_half_up

round(2.675, 2)           # 2.67  (binary floating point + banker's rounding)
round_half_up(2.675, 2)   # 2.68
round_half_up(-2.5, 0)    # -3.0  (halves go away from zero)
```

`round_half_up` rounds the shortest decimal representation of the number (what `repr` / `String(x)` print), so both languages give the same answer.

### Validation and edge cases

Every function validates its input and raises `OddsError` (a `ValueError` subclass in Python, an `Error` subclass in JavaScript). Booleans, strings, `NaN` and infinities are never accepted as numbers.

| Situation | Behaviour |
|---|---|
| Decimal odds `≤ 1` (including `0` and negatives) | `OddsError`. Odds of 1.0 would mean no possible profit and a 100 % probability. |
| Probability `0` or `1` in `probability_to_decimal` | `OddsError` (would be infinite odds or odds of 1.0). |
| Probability `0` or `1` in `expected_value` / `kelly_*` | Allowed: `p = 0` gives EV `= −stake` and Kelly `0`; `p = 1` gives Kelly `1`. |
| American odds between −100 and +100 | `OddsError`. `+100` and `−100` both mean even money (2.0); `decimal_to_american(2.0)` returns `+100`. |
| Indonesian odds in (−1, 1), Malay odds `0` or outside [−1, 1] | `OddsError`. |
| `decimal_to_fractional` for prices very close to 1 | `OddsError` if the closest fraction within `max_denominator` is `0/1`; raise the limit. |
| Market with fewer than 2 prices (margin, fair odds, arbitrage) | `OddsError`. |
| Additive method gives `p ≤ 0` for a long shot | `OddsError` — use another method. |
| Shin method on a market with overround `< 1` | `OddsError` (the model needs a positive margin). |
| Negative edge in Kelly | Returns `0` (never a negative stake). |
| Kelly `fraction` outside (0, 1] | `OddsError`. |
| Negative stake or bankroll; non-positive arbitrage total | `OddsError`. |
| Floating point | Results are IEEE-754 doubles; expect `0.05000000000000004`-style tails and round for display. |

## API

| Python | JavaScript | Returns |
|---|---|---|
| `convert(value, from_format, to_format)` | `convert(value, from, to)` | converted price |
| `to_decimal(value, fmt)` / `from_decimal(odds, fmt)` | `toDecimal` / `fromDecimal` | decimal odds / price in `fmt` |
| `decimal_to_fractional(odds, max_denominator=100)` | `decimalToFractional(odds, maxDenominator?)` | `"n/m"` |
| `fractional_to_decimal(text)` | `fractionalToDecimal(text)` | decimal odds |
| `decimal_to_american` / `american_to_decimal` | `decimalToAmerican` / `americanToDecimal` | |
| `format_american(american, decimals=0)` | `formatAmerican(american, decimals?)` | `"+150"` |
| `decimal_to_hongkong` / `hongkong_to_decimal` | `decimalToHongkong` / `hongkongToDecimal` | |
| `decimal_to_indonesian` / `indonesian_to_decimal` | `decimalToIndonesian` / `indonesianToDecimal` | |
| `decimal_to_malay` / `malay_to_decimal` | `decimalToMalay` / `malayToDecimal` | |
| `implied_probability(odds)` / `probability_to_decimal(p)` | `impliedProbability` / `probabilityToDecimal` | |
| `implied_probabilities(odds)` | `impliedProbabilities(odds)` | `1/d` per outcome |
| `overround(odds)` / `margin(odds)` / `market_payout(odds)` | `overround` / `margin` / `marketPayout` | |
| `fair_probabilities(odds, method="multiplicative")` | `fairProbabilities(odds, method?)` | probabilities summing to 1 |
| `fair_odds(odds, method="multiplicative")` | `fairOdds(odds, method?)` | no-vig decimal odds |
| `shin_z(odds)` | `shinZ(odds)` | Shin's `z` |
| `accumulator_odds(odds)` | `accumulatorOdds(odds)` | product of legs |
| `accumulator_payout(stake, odds, results=None)` | `accumulatorPayout(stake, odds, results?)` | total return |
| `system_combinations(legs, sizes)` | `systemCombinations(legs, sizes)` | leg-index tuples |
| `system_bet(odds, sizes, total_stake)` | `systemBet(odds, sizes, totalStake)` | `SystemBet` |
| `system_payout(odds, sizes, total_stake, results)` | `systemPayout(odds, sizes, totalStake, results)` | total return |
| `expected_value(odds, probability, stake=1)` | `expectedValue(odds, probability, stake?)` | expected profit |
| `kelly_fraction(odds, probability, fraction=1)` | `kellyFraction(odds, probability, fraction?)` | share of bankroll |
| `kelly_stake(bankroll, odds, probability, fraction=1)` | `kellyStake(bankroll, odds, probability, fraction?)` | stake |
| `is_arbitrage(odds)` | `isArbitrage(odds)` | `bool` |
| `arbitrage(odds, total_stake, decimals=None)` | `arbitrage(odds, totalStake, decimals?)` | `Arbitrage` |
| `round_half_up(value, decimals=2)` | `roundHalfUp(value, decimals?)` | rounded number |
| `OddsError`, `FORMATS`, `METHODS`, `RESULTS` | same names | |

## Formulas and references

With decimal odds `d`, implied probability `π = 1/d` and overround `S = Σ πᵢ`:

- **Odds formats.** Fractional odds are the net profit per unit (`d − 1`), American odds the profit on a 100 stake (positive) or the stake needed to win 100 (negative); Hong Kong odds equal `d − 1`, Indonesian odds are American odds / 100 and Malay odds are `−1 / Indonesian`. See [Fixed-odds betting](https://en.wikipedia.org/wiki/Fixed-odds_betting).
- **Overround and margin.** `S − 1` is the bookmaker margin; `1/S` is the theoretical payout. Some sources quote the margin as `1 − 1/S` instead — `1 - market_payout(odds)` gives that. See [Mathematics of bookmaking](https://en.wikipedia.org/wiki/Mathematics_of_bookmaking).
- **Multiplicative, additive and power methods.** Clarke, S., Kovalchik, S. & Ingram, M. (2017). *Adjusting bookmaker's odds to allow for overround.* American Journal of Sports Science, 5(6), 45–49.
- **Shin method.** Shin, H. S. (1993). *Measuring the incidence of insider trading in a market for state-contingent claims.* The Economic Journal, 103(420), 1141–1153. Implementation: `pᵢ(z) = (√(z² + 4(1 − z)πᵢ²/S) − z) / (2(1 − z))`, with `z ∈ [0, 1)` found by bisection so that `Σ pᵢ = 1`, as described in Štrumbelj, E. (2014). *On determining probability forecasts from betting odds.* International Journal of Forecasting, 30(4), 934–943.
- **Kelly criterion.** `f* = (b·p − q) / b` with `b = d − 1`, `q = 1 − p`. Kelly, J. L. (1956). *A new interpretation of information rate.* Bell System Technical Journal, 35(4), 917–926. See [Kelly criterion](https://en.wikipedia.org/wiki/Kelly_criterion).
- **Expected value.** `EV = stake · (p·d − 1)`.
- **Arbitrage.** A market is an arbitrage when `S < 1`; stakes `sᵢ = T·πᵢ/S` return `T/S` whatever happens. See [Arbitrage betting](https://en.wikipedia.org/wiki/Arbitrage_betting).
- **System bets.** Named full-cover bets as in the [Glossary of bets offered by UK bookmakers](https://en.wikipedia.org/wiki/Glossary_of_bets_offered_by_UK_bookmakers); payouts via [elementary symmetric polynomials](https://en.wikipedia.org/wiki/Elementary_symmetric_polynomial).

## Repository layout

```
python/         PyPI package odds-tools (import odds_tools), pytest suite
js/             npm package odds-tools (TypeScript source, ESM + CJS builds), node:test suite
test-vectors/   vectors.json shared by both suites + generate.py (independent reference values)
```

The shared vectors hold 300+ cases (expected values and expected errors). Their expected values are computed independently of both implementations — exact rational arithmetic and 50-digit root finding — so the two packages are tested against the same ground truth rather than against each other.

## Need live odds data?

odds-tools works with prices from any source and needs no API key. If you also need a feed of pre-match and live odds, [SportAPI](https://sportapi.net/sport-line-api.html) provides a commercial sports odds API whose selections carry decimal prices in `oc_rate`, so a market goes straight into the functions above:

```python
from odds_tools import margin, fair_odds

# One betting market from a SportAPI `events` response (shortened)
market = {"group_name": "1X2", "oc_list": [
    {"oc_name": "W1", "oc_rate": 1.36},
    {"oc_name": "X", "oc_rate": 5.35},
    {"oc_name": "W2", "oc_rate": 9.4},
]}
prices = [oc["oc_rate"] for oc in market["oc_list"]]
margin(prices), fair_odds(prices)   # 0.0286, [1.399, 5.503, 9.669]
```

See the [SportAPI documentation](https://sportapi.net/docs/sport-line/data-models/odds.html) for the odds data model and the [quick start](https://sportapi.net/docs/sport-line/getting-started/quick-start.html). Plans start from $30/month with a free 2-day trial; to get an API key, message the [SportAPI bot on Telegram](https://t.me/sportapinet_bot?start=github_odds_tools) or visit [sportapi.net](https://sportapi.net). This library itself is free and MIT-licensed.

## Contributing

Issues and pull requests are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). Any change in behaviour should come with new cases in `test-vectors/` so both packages stay in sync.

## License

[MIT](LICENSE) © 2026 SportAPI
