/**
 * Thrown for every invalid argument (bad price, probability, stake or option),
 * so callers only need to catch one error type.
 */
export class OddsError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'OddsError';
  }
}
