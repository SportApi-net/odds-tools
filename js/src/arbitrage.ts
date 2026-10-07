import { roundHalfUp } from './rounding.js';
import { oddsList, plainSum, positive } from './validate.js';

/** Result of {@link arbitrage}. */
export interface Arbitrage {
  /** True when the prices sum to an overround below 1. */
  readonly isArbitrage: boolean;
  /** Sum of `1 / d` over the outcomes. */
  readonly overround: number;
  /** Theoretical return on the total stake, `1 / overround - 1`. */
  readonly profitMargin: number;
  /** Sum of `stakes` (differs from the requested amount after rounding). */
  readonly totalStake: number;
  readonly stakes: readonly number[];
  /** Return for each outcome if it wins: `stake * odds`. */
  readonly payouts: readonly number[];
  /** Guaranteed profit: `min(payouts) - totalStake` (negative if not an arbitrage). */
  readonly profit: number;
}

/** True if backing every outcome at these prices guarantees a profit. */
export function isArbitrage(odds: readonly number[]): boolean {
  return plainSum(oddsList(odds, 2).map((d) => 1 / d)) < 1;
}

/**
 * Split `totalStake` across the outcomes so every outcome returns the same.
 *
 * `odds` are the best decimal prices for each outcome of one market (2-way,
 * 3-way or more), possibly from different bookmakers. Stakes are proportional
 * to `1 / d`. Pass `decimals` (2 for cents, 0 for whole units) to round each
 * stake half-up; payouts and profit are then computed from the rounded stakes.
 */
export function arbitrage(odds: readonly number[], totalStake: number, decimals?: number): Arbitrage {
  const prices = oddsList(odds, 2);
  const amount = positive(totalStake, 'totalStake');
  const implied = prices.map((d) => 1 / d);
  const book = plainSum(implied);
  let stakes = implied.map((p) => (amount * p) / book);
  if (decimals !== undefined) stakes = stakes.map((s) => roundHalfUp(s, decimals));
  const payouts = stakes.map((s, i) => s * (prices[i] as number));
  const staked = plainSum(stakes);
  return {
    isArbitrage: book < 1,
    overround: book,
    profitMargin: 1 / book - 1,
    totalStake: staked,
    stakes,
    payouts,
    profit: Math.min(...payouts) - staked,
  };
}
