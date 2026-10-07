# odds-tools (JavaScript / TypeScript)

Dependency-free betting-odds math: format conversion, bookmaker margin, no-vig fair odds (multiplicative, additive, power, Shin), accumulators, system bets, Kelly staking, expected value and arbitrage. Written in TypeScript, shipped as ESM and CommonJS with type definitions.

The same API is available for Python as the [`odds-tools` PyPI package](https://pypi.org/project/odds-tools/); both are tested against one shared set of test vectors.

```bash
npm install odds-tools
```

## Examples

```ts
import {
  convert, formatAmerican, decimalToAmerican,
  margin, fairOdds, fairProbabilities,
  accumulatorPayout, systemBet, systemPayout,
  expectedValue, kellyStake, arbitrage, roundHalfUp, OddsError,
} from 'odds-tools';
// CommonJS: const { convert } = require('odds-tools');

// Conversions: decimal, fractional, american, hongkong, indonesian, malay, probability
convert('5/2', 'fractional', 'decimal');       // 3.5
convert(-110, 'american', 'fractional');       // '10/11' (typed as string)
convert(1.5, 'hongkong', 'malay');             // -0.667
formatAmerican(decimalToAmerican(1.91));       // '-110'

// Margin and fair odds of one market (1X2)
const prices = [1.36, 5.35, 9.4];
margin(prices);                                // 0.0286 -> 2.86 %
fairOdds(prices);                              // [1.399, 5.503, 9.669]  multiplicative
fairProbabilities(prices, 'shin');             // [0.723, 0.178, 0.099]

// Accumulator with a void leg, and a 2/3 system bet
accumulatorPayout(10, [1.91, 1.83, 2.05], ['win', 'void', 'win']);   // 39.155
systemBet([1.9, 2.1, 2.4], 2, 30);             // { bets: 3, unitStake: 10, maxPayout: 135.9, ... }
systemPayout([1.9, 2.1, 2.4], 2, 30, ['win', 'win', 'lose']);        // 39.9

// Value and staking
expectedValue(2.2, 0.5, 100);                  // 10
kellyStake(1000, 2.2, 0.5, 0.5);               // 41.67 (half Kelly)

// Arbitrage across bookmakers, stakes rounded to cents
const arb = arbitrage([2.1, 2.05], 100, 2);
console.log(arb.stakes, arb.profit);           // [49.4, 50.6] 3.73

roundHalfUp(2.675, 2);                         // 2.68 ((2.675).toFixed(2) gives '2.67')

try {
  convert(50, 'american', 'decimal');
} catch (err) {
  if (err instanceof OddsError) console.log(err.message);
  // american odds must be >= +100 or <= -100 (got 50)
}
```

Outputs in comments are rounded; functions return full-precision numbers.

## Edge cases

- Decimal odds must be `> 1`; `0`, `1`, negatives, `NaN`, `Infinity`, booleans, strings and `null` throw `OddsError`.
- `probabilityToDecimal` needs `0 < p < 1`; `expectedValue` and `kelly*` accept `0 <= p <= 1`.
- American odds between −100 and +100 are invalid; `decimalToAmerican(2)` returns `100`.
- The additive method throws if a long shot would get a non-positive probability; the Shin method needs an overround `>= 1`.
- Kelly never returns a negative stake (no edge -> `0`).

Full documentation, formulas and references: <https://github.com/SportApi-net/odds-tools#readme>

## Need live odds data?

odds-tools needs no API key and works with prices from any source. For a commercial feed of pre-match and live decimal odds, see [SportAPI](https://sportapi.net/sport-line-api.html) and the [SportAPI documentation](https://sportapi.net/docs/sport-line/data-models/odds.html) (from $30/month, free 2-day trial; [get a key via Telegram](https://t.me/sportapinet_bot?start=github_odds_tools)).

## License

MIT © 2026 SportAPI
