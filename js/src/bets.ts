import { OddsError } from './errors.js';
import { integer, nonNegative, oddsList, plainSum, show } from './validate.js';

/** Allowed leg results. `true`/`false` are accepted as `win`/`lose`. */
export const RESULTS = ['win', 'lose', 'void'] as const;
export type LegResult = (typeof RESULTS)[number] | boolean;

/** Summary of a system bet; see {@link systemBet}. */
export interface SystemBet {
  /** Number of selections. */
  readonly legs: number;
  /** Accumulator sizes included, ascending (`[2]` for a 2/3 system). */
  readonly sizes: readonly number[];
  /** Number of combinations (`C(n, k)` summed over sizes). */
  readonly bets: number;
  /** Stake on each combination: `totalStake / bets`. */
  readonly unitStake: number;
  readonly totalStake: number;
  /** Total return if every selection wins. */
  readonly maxPayout: number;
}

/** Combined decimal odds of an accumulator: the product of all legs. */
export function accumulatorOdds(odds: readonly number[]): number {
  let result = 1;
  for (const d of oddsList(odds, 1)) result *= d;
  return result;
}

/**
 * Total return of an accumulator (stake included).
 *
 * Without `results` every leg is assumed to win. With `results` (`'win'`,
 * `'lose'`, `'void'` or a boolean per leg) a lost leg makes the payout 0 and a
 * void leg counts as odds of 1.
 */
export function accumulatorPayout(
  stake: number,
  odds: readonly number[],
  results?: readonly LegResult[],
): number {
  const amount = nonNegative(stake, 'stake');
  const prices = oddsList(odds, 1);
  const factors = results === undefined ? prices : toFactors(prices, results);
  let result = amount;
  for (const f of factors) result *= f;
  return result;
}

/**
 * All leg-index combinations of a system, smallest size first.
 *
 * @example systemCombinations(3, 2) // [[0, 1], [0, 2], [1, 2]]
 */
export function systemCombinations(legs: number, sizes: number | readonly number[]): number[][] {
  const n = integer(legs, 'legs');
  if (n < 1) throw new OddsError(`legs must be at least 1 (got ${show(legs)})`);
  const out: number[][] = [];
  for (const k of checkSizes(sizes, n)) {
    const pick: number[] = [];
    const walk = (start: number): void => {
      if (pick.length === k) {
        out.push([...pick]);
        return;
      }
      for (let i = start; i <= n - (k - pick.length); i++) {
        pick.push(i);
        walk(i + 1);
        pick.pop();
      }
    };
    walk(0);
  }
  return out;
}

/**
 * Describe a system bet: number of bets, stake split and maximum payout.
 *
 * `sizes` is the accumulator size (`2` for a 2/3 system) or a list of sizes
 * for full-cover bets (`[2, 3, 4]` on 4 legs is a Yankee, 11 bets).
 * `totalStake` is split equally across all combinations.
 */
export function systemBet(
  odds: readonly number[],
  sizes: number | readonly number[],
  totalStake: number,
): SystemBet {
  const prices = oddsList(odds, 1);
  const ks = checkSizes(sizes, prices.length);
  const stake = nonNegative(totalStake, 'totalStake');
  let bets = 0;
  for (const k of ks) bets += binomial(prices.length, k);
  const unit = stake / bets;
  return {
    legs: prices.length,
    sizes: ks,
    bets,
    unitStake: unit,
    totalStake: stake,
    maxPayout: unit * combinationSum(prices, ks),
  };
}

/**
 * Total return of a system bet once results are known.
 *
 * Each combination pays `unitStake * product(odds)` if none of its legs lost
 * (void legs count as odds of 1) and 0 otherwise. Combinations are never
 * enumerated: the sum over all k-leg subsets is the elementary symmetric
 * polynomial e_k.
 */
export function systemPayout(
  odds: readonly number[],
  sizes: number | readonly number[],
  totalStake: number,
  results: readonly LegResult[],
): number {
  const bet = systemBet(odds, sizes, totalStake);
  const factors = toFactors(oddsList(odds, 1), results);
  return bet.unitStake * combinationSum(factors, bet.sizes);
}

function binomial(n: number, k: number): number {
  let result = 1;
  for (let i = 1; i <= k; i++) result = (result * (n - k + i)) / i;
  return result;
}

/** Sum over k in sizes of e_k(factors), the sum of products of all k-subsets. */
function combinationSum(factors: readonly number[], sizes: readonly number[]): number {
  const top = Math.max(...sizes);
  const e = [1, ...new Array<number>(top).fill(0)];
  for (const f of factors) {
    for (let k = top; k > 0; k--) e[k] = (e[k] as number) + (e[k - 1] as number) * f;
  }
  return plainSum(sizes.map((k) => e[k] as number));
}

function checkSizes(sizes: unknown, legs: number): number[] {
  const raw: unknown[] = Array.isArray(sizes) ? [...(sizes as unknown[])] : [sizes];
  if (raw.length === 0) throw new OddsError('sizes must not be empty');
  const values = [...new Set(raw.map((k) => integer(k, 'size')))].sort((a, b) => a - b);
  for (const k of values) {
    if (k < 1 || k > legs) {
      throw new OddsError(`system size must be between 1 and ${legs} (got ${k})`);
    }
  }
  return values;
}

function toFactors(prices: number[], results: unknown): number[] {
  if (!Array.isArray(results)) {
    throw new OddsError(`results must be an array with one entry per leg (got ${show(results)})`);
  }
  if (results.length !== prices.length) {
    throw new OddsError(
      `results must have one entry per leg (${prices.length}), got ${results.length}`,
    );
  }
  return prices.map((price, i) => {
    const result: unknown = results[i];
    if (result === true || result === 'win') return price;
    if (result === false || result === 'lose') return 0;
    if (result === 'void') return 1;
    throw new OddsError(
      `results[${i}] must be 'win', 'lose', 'void', true or false (got ${show(result)})`,
    );
  });
}
