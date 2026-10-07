# odds-tools (Python)

Dependency-free betting-odds math: format conversion, bookmaker margin, no-vig fair odds (multiplicative, additive, power, Shin), accumulators, system bets, Kelly staking, expected value and arbitrage. Typed, tested, Python 3.9+.

The same API is available for JavaScript/TypeScript as the [`odds-tools` npm package](https://www.npmjs.com/package/odds-tools); both are tested against one shared set of test vectors.

```bash
pip install odds-tools
```

## Examples

```python
from odds_tools import (
    convert,
    format_american,
    decimal_to_american,
    margin,
    fair_odds,
    fair_probabilities,
    accumulator_payout,
    system_bet,
    system_payout,
    expected_value,
    kelly_stake,
    arbitrage,
    round_half_up,
    OddsError,
)

# Conversions: decimal, fractional, american, hongkong, indonesian, malay, probability
convert("5/2", "fractional", "decimal")  # 3.5
convert(-110, "american", "fractional")  # '10/11'
convert(1.5, "hongkong", "malay")  # -0.667
format_american(decimal_to_american(1.91))  # '-110'

# Margin and fair odds of one market (1X2)
prices = [1.36, 5.35, 9.4]
margin(prices)  # 0.0286 -> 2.86 %
fair_odds(prices)  # [1.399, 5.503, 9.669]  multiplicative
fair_probabilities(prices, "shin")  # [0.723, 0.178, 0.099]

# Accumulator with a void leg, and a 2/3 system bet
accumulator_payout(10, [1.91, 1.83, 2.05], ["win", "void", "win"])  # 39.155
system_bet([1.9, 2.1, 2.4], 2, 30)  # 3 bets of 10.0, max payout 135.9
system_payout([1.9, 2.1, 2.4], 2, 30, ["win", "win", "lose"])  # 39.9

# Value and staking
expected_value(2.2, probability=0.5, stake=100)  # 10.0
kelly_stake(1000, 2.2, probability=0.5, fraction=0.5)  # 41.67 (half Kelly)

# Arbitrage across bookmakers, stakes rounded to cents
arb = arbitrage([2.1, 2.05], total_stake=100, decimals=2)
arb.stakes, arb.profit  # (49.4, 50.6), 3.73

round_half_up(2.675, 2)  # 2.68 (built-in round gives 2.67)

try:
    convert(50, "american", "decimal")
except OddsError as exc:  # OddsError is a ValueError
    print(exc)  # american odds must be >= +100 or <= -100 (got 50)
```

Outputs in comments are rounded; functions return full-precision floats.

## Edge cases

- Decimal odds must be `> 1`; `0`, `1.0`, negatives, `NaN`, infinities, booleans and strings raise `OddsError`.
- `probability_to_decimal` needs `0 < p < 1`; `expected_value` and `kelly_*` accept `0 <= p <= 1`.
- American odds between −100 and +100 are invalid; `decimal_to_american(2.0)` returns `+100`.
- The additive method raises if a long shot would get a non-positive probability; the Shin method needs an overround `>= 1`.
- Kelly never returns a negative stake (no edge -> `0`).

Full documentation, formulas and references: <https://github.com/SportApi-net/odds-tools#readme>

## Need live odds data?

odds-tools needs no API key and works with prices from any source. For a commercial feed of pre-match and live decimal odds, see [SportAPI](https://sportapi.net/sport-line-api.html) and the [SportAPI documentation](https://sportapi.net/docs/sport-line/data-models/odds.html) (from $30/month, free 2-day trial; [get a key via Telegram](https://t.me/sportapinet_bot?start=github_odds_tools)).

## License

MIT © 2026 SportAPI
