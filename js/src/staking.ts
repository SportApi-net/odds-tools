import { OddsError } from './errors.js';
import { decimalOdds, nonNegative, number, probability as checkProbability, show } from './validate.js';

/**
 * Expected profit of a bet: `stake * (p * d - 1)`.
 *
 * With the default `stake = 1` this is the edge (ROI per unit staked):
 * `expectedValue(2.1, 0.5)` is 0.05, i.e. +5 %.
 */
export function expectedValue(odds: number, probability: number, stake = 1): number {
  const d = decimalOdds(odds);
  const p = checkProbability(probability);
  const amount = nonNegative(stake, 'stake');
  return amount * (p * d - 1);
}

/**
 * Share of the bankroll to stake according to the Kelly criterion.
 *
 * Full Kelly is `f* = (b p - q) / b = (p d - 1) / (d - 1)` with `b = d - 1`
 * and `q = 1 - p`, multiplied by `fraction` (`0.5` = half Kelly). Returns 0
 * when the bet has no positive edge.
 */
export function kellyFraction(odds: number, probability: number, fraction = 1): number {
  const d = decimalOdds(odds);
  const p = checkProbability(probability);
  const share = number(fraction, 'fraction');
  if (!(share > 0 && share <= 1)) {
    throw new OddsError(`fraction must be in (0, 1] (got ${show(fraction)})`);
  }
  const full = (p * d - 1) / (d - 1);
  return full <= 0 ? 0 : full * share;
}

/** Kelly stake in money: `bankroll * kellyFraction(odds, probability, fraction)`. */
export function kellyStake(bankroll: number, odds: number, probability: number, fraction = 1): number {
  const amount = nonNegative(bankroll, 'bankroll');
  return amount * kellyFraction(odds, probability, fraction);
}
