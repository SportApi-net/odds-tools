/**
 * Dependency-free betting-odds math: conversions, margin, fair odds,
 * accumulators, system bets, Kelly staking, expected value and arbitrage.
 *
 * All prices are decimal odds unless a function name says otherwise. Invalid
 * input throws {@link OddsError}.
 *
 * @packageDocumentation
 */
export { OddsError } from './errors.js';
export { type Arbitrage, arbitrage, isArbitrage } from './arbitrage.js';
export {
  RESULTS,
  type LegResult,
  type SystemBet,
  accumulatorOdds,
  accumulatorPayout,
  systemBet,
  systemCombinations,
  systemPayout,
} from './bets.js';
export {
  FORMATS,
  type NumericFormat,
  type OddsFormat,
  americanToDecimal,
  convert,
  decimalToAmerican,
  decimalToFractional,
  decimalToHongkong,
  decimalToIndonesian,
  decimalToMalay,
  formatAmerican,
  fractionalToDecimal,
  fromDecimal,
  hongkongToDecimal,
  impliedProbability,
  indonesianToDecimal,
  malayToDecimal,
  probabilityToDecimal,
  toDecimal,
} from './convert.js';
export {
  METHODS,
  type DevigMethod,
  fairOdds,
  fairProbabilities,
  impliedProbabilities,
  margin,
  marketPayout,
  overround,
  shinZ,
} from './margin.js';
export { roundHalfUp } from './rounding.js';
export { expectedValue, kellyFraction, kellyStake } from './staking.js';
