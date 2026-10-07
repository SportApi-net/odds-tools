import { OddsError } from './errors.js';

/** Human-readable rendering of a bad value for error messages. */
export function show(value: unknown): string {
  if (typeof value === 'string') return JSON.stringify(value);
  if (typeof value === 'number' || typeof value === 'boolean' || value == null) {
    return String(value);
  }
  try {
    return JSON.stringify(value) ?? String(value);
  } catch {
    return String(value);
  }
}

export function number(value: unknown, name: string): number {
  if (typeof value !== 'number') {
    throw new OddsError(`${name} must be a number (got ${show(value)})`);
  }
  if (!Number.isFinite(value)) {
    throw new OddsError(`${name} must be a finite number (got ${show(value)})`);
  }
  return value;
}

export function integer(value: unknown, name: string): number {
  if (typeof value !== 'number' || !Number.isInteger(value)) {
    throw new OddsError(`${name} must be an integer (got ${show(value)})`);
  }
  return value;
}

/** Decimal odds must be a finite number strictly greater than 1. */
export function decimalOdds(value: unknown, name = 'odds'): number {
  const result = number(value, name);
  if (result <= 1) {
    throw new OddsError(`${name} must be greater than 1 (got ${show(value)})`);
  }
  return result;
}

export function oddsList(values: unknown, minLength: number, name = 'odds'): number[] {
  if (!Array.isArray(values)) {
    throw new OddsError(`${name} must be an array of decimal odds (got ${show(values)})`);
  }
  if (values.length < minLength) {
    throw new OddsError(
      `${name} must contain at least ${minLength} price(s) (got ${values.length})`,
    );
  }
  return values.map((v: unknown, i) => decimalOdds(v, `${name}[${i}]`));
}

/** A probability in the closed interval [0, 1]. */
export function probability(value: unknown, name = 'probability'): number {
  const result = number(value, name);
  if (!(result >= 0 && result <= 1)) {
    throw new OddsError(`${name} must be between 0 and 1 (got ${show(value)})`);
  }
  return result;
}

export function nonNegative(value: unknown, name: string): number {
  const result = number(value, name);
  if (result < 0) {
    throw new OddsError(`${name} must not be negative (got ${show(value)})`);
  }
  return result;
}

export function positive(value: unknown, name: string): number {
  const result = number(value, name);
  if (result <= 0) {
    throw new OddsError(`${name} must be greater than 0 (got ${show(value)})`);
  }
  return result;
}

/** Left-to-right sum; mirrors the Python package exactly. */
export function plainSum(values: readonly number[]): number {
  let total = 0;
  for (const v of values) total += v;
  return total;
}

/**
 * Shortest round-trip decimal representation of a finite number without
 * exponent notation, e.g. 1e21 -> "1000000000000000000000", 1.5e-7 -> "0.00000015".
 * Uses the same digits as Python's repr().
 */
export function plainDecimalString(value: number): string {
  const text = String(Math.abs(value));
  const sign = value < 0 ? '-' : '';
  const match = /^(\d+)(?:\.(\d+))?e([+-]\d+)$/.exec(text);
  if (match === null) return sign + text;
  const intDigits = match[1] as string;
  const fracDigits = match[2] ?? '';
  const exponent = Number(match[3]);
  const digits = intDigits + fracDigits;
  const point = intDigits.length + exponent;
  if (point <= 0) return `${sign}0.${'0'.repeat(-point)}${digits}`;
  if (point >= digits.length) return sign + digits + '0'.repeat(point - digits.length);
  return `${sign}${digits.slice(0, point)}.${digits.slice(point)}`;
}
