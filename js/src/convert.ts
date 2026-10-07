import { OddsError } from './errors.js';
import { roundHalfUp } from './rounding.js';
import { decimalOdds, integer, number, plainDecimalString, show } from './validate.js';

/** Supported odds formats; decimal odds are the hub every conversion goes through. */
export const FORMATS = [
  'decimal',
  'fractional',
  'american',
  'hongkong',
  'indonesian',
  'malay',
  'probability',
] as const;

export type OddsFormat = (typeof FORMATS)[number];
export type NumericFormat = Exclude<OddsFormat, 'fractional'>;

const FRACTION_RE = /^\s*(\d+)\s*\/\s*(\d+)\s*$/;
const EVENS = new Set(['evens', 'evs', 'even']);

// --- fractional ---------------------------------------------------------------

/** `"5/2"` -> `3.5`. `"evens"` (or `"evs"`) is accepted as `"1/1"`. */
export function fractionalToDecimal(fraction: string): number {
  if (typeof fraction !== 'string') {
    throw new OddsError(`fractional odds must be a string like '5/2' (got ${show(fraction)})`);
  }
  if (EVENS.has(fraction.trim().toLowerCase())) return 2;
  const match = FRACTION_RE.exec(fraction);
  if (match === null) {
    throw new OddsError(`fractional odds must look like '5/2' (got ${show(fraction)})`);
  }
  const numerator = Number(match[1]);
  const denominator = Number(match[2]);
  if (numerator === 0 || denominator === 0) {
    throw new OddsError(
      `fractional odds need a positive numerator and denominator (got ${show(fraction)})`,
    );
  }
  return 1 + numerator / denominator;
}

/**
 * `3.5` -> `"5/2"`.
 *
 * The decimal price is read as written (1.91 is exactly 191/100), reduced and,
 * if its denominator exceeds `maxDenominator`, replaced by the closest fraction
 * whose denominator is at most `maxDenominator` (same algorithm as Python's
 * `Fraction.limit_denominator`). Throws if that closest fraction would be 0/1.
 */
export function decimalToFractional(odds: number, maxDenominator = 100): string {
  const d = decimalOdds(odds);
  const limit = integer(maxDenominator, 'maxDenominator');
  if (limit < 1) {
    throw new OddsError(`maxDenominator must be at least 1 (got ${show(maxDenominator)})`);
  }
  const [intPart = '0', fracPart = ''] = plainDecimalString(d).split('.');
  let den = 10n ** BigInt(fracPart.length);
  let num = BigInt(intPart + fracPart) - den; // profit part: d - 1
  const g = gcd(num, den);
  num /= g;
  den /= g;
  if (den > BigInt(limit)) [num, den] = limitDenominator(num, den, BigInt(limit));
  if (num === 0n) {
    throw new OddsError(
      `odds ${show(d)} cannot be written as a fraction with denominator <= ${limit}`,
    );
  }
  return `${num}/${den}`;
}

function gcd(a: bigint, b: bigint): bigint {
  while (b !== 0n) [a, b] = [b, a % b];
  return a < 0n ? -a : a;
}

function abs(x: bigint): bigint {
  return x < 0n ? -x : x;
}

/** Closest fraction to num/den (num >= 0) with denominator <= max. */
function limitDenominator(num: bigint, den: bigint, max: bigint): [bigint, bigint] {
  let p0 = 0n;
  let q0 = 1n;
  let p1 = 1n;
  let q1 = 0n;
  let n = num;
  let d = den;
  for (;;) {
    const a = n / d;
    const q2 = q0 + a * q1;
    if (q2 > max) break;
    [p0, q0, p1, q1] = [p1, q1, p0 + a * p1, q2];
    [n, d] = [d, n - a * d];
  }
  const k = (max - q0) / q1;
  const bound1n = p0 + k * p1;
  const bound1d = q0 + k * q1;
  // |p1/q1 - num/den| <= |bound1 - num/den|  (cross-multiplied)
  const dist2 = abs(p1 * den - num * q1) * bound1d;
  const dist1 = abs(bound1n * den - num * bound1d) * q1;
  return dist2 <= dist1 ? [p1, q1] : [bound1n, bound1d];
}

// --- american (moneyline) -------------------------------------------------------

/** `+150` -> `2.5`; `-200` -> `1.5`. Values between -100 and +100 are invalid. */
export function americanToDecimal(american: number): number {
  const a = number(american, 'american odds');
  if (a >= 100) return 1 + a / 100;
  if (a <= -100) return 1 + 100 / -a;
  throw new OddsError(`american odds must be >= +100 or <= -100 (got ${show(american)})`);
}

/** `2.5` -> `150`; `1.5` -> `-200`. Even money (2.0) is `+100`. */
export function decimalToAmerican(odds: number): number {
  const d = decimalOdds(odds);
  if (d >= 2) return (d - 1) * 100;
  return -100 / (d - 1);
}

/** Format a moneyline price with an explicit sign: `150` -> `"+150"`. */
export function formatAmerican(american: number, decimals = 0): string {
  const a = number(american, 'american odds');
  if (a > -100 && a < 100) {
    throw new OddsError(`american odds must be >= +100 or <= -100 (got ${show(american)})`);
  }
  const rounded = roundHalfUp(a, decimals);
  return (rounded > 0 ? '+' : '-') + Math.abs(rounded).toFixed(decimals);
}

// --- Asian formats -----------------------------------------------------------------

/** Hong Kong odds are the net profit per unit staked: `1.5` -> `2.5`. */
export function hongkongToDecimal(hongkong: number): number {
  const h = number(hongkong, 'hong kong odds');
  if (h <= 0) throw new OddsError(`hong kong odds must be greater than 0 (got ${show(hongkong)})`);
  return 1 + h;
}

export function decimalToHongkong(odds: number): number {
  return decimalOdds(odds) - 1;
}

/** Indonesian odds are American odds divided by 100: `-2` -> `1.5`. */
export function indonesianToDecimal(indonesian: number): number {
  const i = number(indonesian, 'indonesian odds');
  if (i >= 1) return 1 + i;
  if (i <= -1) return 1 + 1 / -i;
  throw new OddsError(`indonesian odds must be >= 1 or <= -1 (got ${show(indonesian)})`);
}

export function decimalToIndonesian(odds: number): number {
  const d = decimalOdds(odds);
  return d >= 2 ? d - 1 : -1 / (d - 1);
}

/** Malay odds: positive values in (0, 1], negative values in [-1, 0). */
export function malayToDecimal(malay: number): number {
  const m = number(malay, 'malay odds');
  if (m > 0 && m <= 1) return 1 + m;
  if (m >= -1 && m < 0) return 1 + 1 / -m;
  throw new OddsError(`malay odds must be in (0, 1] or [-1, 0) (got ${show(malay)})`);
}

export function decimalToMalay(odds: number): number {
  const d = decimalOdds(odds);
  return d <= 2 ? d - 1 : -1 / (d - 1);
}

// --- probability -------------------------------------------------------------------

/** Raw implied probability `1 / d` (still includes the bookmaker margin). */
export function impliedProbability(odds: number): number {
  return 1 / decimalOdds(odds);
}

/** `0.4` -> `2.5`. The probability must be strictly between 0 and 1. */
export function probabilityToDecimal(probability: number): number {
  const p = number(probability, 'probability');
  if (!(p > 0 && p < 1)) {
    throw new OddsError(`probability must be strictly between 0 and 1 (got ${show(probability)})`);
  }
  return 1 / p;
}

// --- generic -----------------------------------------------------------------------

function checkFormat(name: unknown, argument: string): OddsFormat {
  if (typeof name !== 'string' || !(FORMATS as readonly string[]).includes(name)) {
    throw new OddsError(`${argument} must be one of ${FORMATS.join(', ')} (got ${show(name)})`);
  }
  return name as OddsFormat;
}

/** Convert a price in `from` format to decimal odds. */
export function toDecimal(value: number | string, from: OddsFormat): number {
  switch (checkFormat(from, 'from')) {
    case 'decimal':
      return decimalOdds(value);
    case 'fractional':
      return fractionalToDecimal(value as string);
    case 'american':
      return americanToDecimal(value as number);
    case 'hongkong':
      return hongkongToDecimal(value as number);
    case 'indonesian':
      return indonesianToDecimal(value as number);
    case 'malay':
      return malayToDecimal(value as number);
    case 'probability':
      return probabilityToDecimal(value as number);
  }
}

/** Convert decimal odds to the `to` format. */
export function fromDecimal(odds: number, to: 'fractional'): string;
export function fromDecimal(odds: number, to: NumericFormat): number;
export function fromDecimal(odds: number, to: OddsFormat): number | string;
export function fromDecimal(odds: number, to: OddsFormat): number | string {
  switch (checkFormat(to, 'to')) {
    case 'decimal':
      return decimalOdds(odds);
    case 'fractional':
      return decimalToFractional(odds);
    case 'american':
      return decimalToAmerican(odds);
    case 'hongkong':
      return decimalToHongkong(odds);
    case 'indonesian':
      return decimalToIndonesian(odds);
    case 'malay':
      return decimalToMalay(odds);
    case 'probability':
      return impliedProbability(odds);
  }
}

/**
 * Convert a price between any two formats.
 *
 * @example convert('3/2', 'fractional', 'american') // 150
 */
export function convert(value: number | string, from: OddsFormat, to: 'fractional'): string;
export function convert(value: number | string, from: OddsFormat, to: NumericFormat): number;
export function convert(value: number | string, from: OddsFormat, to: OddsFormat): number | string;
export function convert(value: number | string, from: OddsFormat, to: OddsFormat): number | string {
  return fromDecimal(toDecimal(value, from), to);
}
