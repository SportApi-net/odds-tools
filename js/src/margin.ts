import { OddsError } from './errors.js';
import { oddsList, plainSum, show } from './validate.js';

/** Margin-removal methods supported by {@link fairProbabilities}. */
export const METHODS = ['multiplicative', 'additive', 'power', 'shin'] as const;
export type DevigMethod = (typeof METHODS)[number];

// Fixed number of bisection steps so both packages perform identical operations.
const BISECTION_STEPS = 200;

/** `1 / d` for every price. They sum to the overround, not to 1. */
export function impliedProbabilities(odds: readonly number[]): number[] {
  return oddsList(odds, 1).map((d) => 1 / d);
}

/** Sum of implied probabilities, e.g. `1.05` for a 5 % book. */
export function overround(odds: readonly number[]): number {
  return plainSum(impliedProbabilities(oddsList(odds, 2)));
}

/** Bookmaker margin `overround - 1` (`0.05` = 5 %). Negative means arbitrage. */
export function margin(odds: readonly number[]): number {
  return overround(odds) - 1;
}

/** Theoretical payout (return to player) `1 / overround`, e.g. `0.952`. */
export function marketPayout(odds: readonly number[]): number {
  return 1 / overround(odds);
}

/**
 * Remove the margin and return probabilities that sum to 1.
 *
 * - `multiplicative`: `p_i = pi_i / S` (normalisation, the common default).
 * - `additive`: `p_i = pi_i - (S - 1) / n`; throws if a long shot would get `p <= 0`.
 * - `power`: `p_i = pi_i ** k` with `k` chosen so the sum is 1.
 * - `shin`: Shin (1993) insider-trading model; needs a positive margin.
 *
 * where `pi_i = 1 / d_i` and `S` is their sum.
 */
export function fairProbabilities(
  odds: readonly number[],
  method: DevigMethod = 'multiplicative',
): number[] {
  const prices = oddsList(odds, 2);
  if (typeof method !== 'string' || !(METHODS as readonly string[]).includes(method)) {
    throw new OddsError(`method must be one of ${METHODS.join(', ')} (got ${show(method)})`);
  }
  const implied = prices.map((d) => 1 / d);
  const total = plainSum(implied);
  switch (method) {
    case 'multiplicative':
      return implied.map((p) => p / total);
    case 'additive':
      return additive(implied, total);
    case 'power':
      return power(implied);
    case 'shin':
      return shin(implied, total);
  }
}

/** Decimal odds without the margin: `1 / p` for {@link fairProbabilities}. */
export function fairOdds(odds: readonly number[], method: DevigMethod = 'multiplicative'): number[] {
  return fairProbabilities(odds, method).map((p) => 1 / p);
}

/** Shin's `z`: the estimated share of money from insiders (0 for a fair book). */
export function shinZ(odds: readonly number[]): number {
  const implied = oddsList(odds, 2).map((d) => 1 / d);
  const total = plainSum(implied);
  checkShin(total);
  return solveShinZ(implied, total);
}

function additive(implied: number[], total: number): number[] {
  const share = (total - 1) / implied.length;
  const result = implied.map((p) => p - share);
  result.forEach((p, i) => {
    if (p <= 0) {
      throw new OddsError(
        `additive method gives a non-positive probability for outcome ${i} ` +
          '(margin is larger than its implied probability); ' +
          "use 'multiplicative', 'power' or 'shin' instead",
      );
    }
  });
  return result;
}

function power(implied: number[]): number[] {
  const excess = (k: number): number => plainSum(implied.map((p) => p ** k)) - 1;
  // excess(k) decreases in k and excess(0) = n - 1 > 0.
  let lo = 0;
  let hi = 1;
  while (excess(hi) > 0) {
    lo = hi;
    hi *= 2;
  }
  for (let i = 0; i < BISECTION_STEPS; i++) {
    const mid = (lo + hi) / 2;
    if (excess(mid) > 0) lo = mid;
    else hi = mid;
  }
  const k = (lo + hi) / 2;
  const powered = implied.map((p) => p ** k);
  const total = plainSum(powered);
  return powered.map((p) => p / total);
}

function checkShin(total: number): void {
  if (total < 1) {
    throw new OddsError(
      'the Shin method needs a market with a positive margin (overround > 1); ' +
        `this market has an overround of ${total}`,
    );
  }
}

function shinProbabilities(implied: number[], total: number, z: number): number[] {
  return implied.map((p) => (Math.sqrt(z * z + (4 * (1 - z) * p * p) / total) - z) / (2 * (1 - z)));
}

function solveShinZ(implied: number[], total: number): number {
  if (total === 1) return 0;
  // sum(p(z)) - 1 is sqrt(S) - 1 > 0 at z = 0 and tends to
  // sum(pi^2) / S - 1 < 0 as z -> 1, so bisection on [0, 1) finds the root.
  let lo = 0;
  let hi = 1;
  for (let i = 0; i < BISECTION_STEPS; i++) {
    const mid = (lo + hi) / 2;
    if (mid === lo || mid === hi) break;
    if (plainSum(shinProbabilities(implied, total, mid)) > 1) lo = mid;
    else hi = mid;
  }
  return (lo + hi) / 2;
}

function shin(implied: number[], total: number): number[] {
  checkShin(total);
  const z = solveShinZ(implied, total);
  if (z === 0) return implied.map((p) => p / total);
  const probabilities = shinProbabilities(implied, total, z);
  const norm = plainSum(probabilities);
  return probabilities.map((p) => p / norm);
}
