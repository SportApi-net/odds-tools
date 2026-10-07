import { OddsError } from './errors.js';
import { integer, number, plainDecimalString, show } from './validate.js';

/**
 * Round `value` to `decimals` places, halves away from zero.
 *
 * Works on the shortest decimal representation of the number, so
 * `roundHalfUp(2.675, 2) === 2.68` (while `Math.round(2.675 * 100) / 100`
 * and `(2.675).toFixed(2)` give 2.67 because of binary floating point).
 */
export function roundHalfUp(value: number, decimals = 2): number {
  const x = number(value, 'value');
  const places = integer(decimals, 'decimals');
  if (places < 0 || places > 15) {
    throw new OddsError(`decimals must be between 0 and 15 (got ${show(decimals)})`);
  }
  const text = plainDecimalString(Math.abs(x));
  const [intPart = '0', fracPart = ''] = text.split('.');
  if (fracPart.length <= places) return x;
  let scaled = BigInt(intPart + fracPart.slice(0, places));
  if ((fracPart[places] as string) >= '5') scaled += 1n;
  const digits = scaled.toString().padStart(places + 1, '0');
  const cut = digits.length - places;
  const result = Number(places === 0 ? digits : `${digits.slice(0, cut)}.${digits.slice(cut)}`);
  return x < 0 ? -result : result;
}
