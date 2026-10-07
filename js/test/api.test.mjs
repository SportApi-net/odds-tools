// Behaviour and property tests that complement the shared vectors.
import assert from 'node:assert/strict';
import { test } from 'node:test';

import * as ot from '../dist/esm/index.js';

/** Small deterministic PRNG (mulberry32) so property tests are reproducible. */
function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const close = (a, b, eps = 1e-12) => Math.abs(a - b) <= eps * Math.max(1, Math.abs(b));

test('OddsError is an Error with a clear message', () => {
  assert.throws(() => ot.impliedProbability(1), (err) => {
    assert.ok(err instanceof ot.OddsError);
    assert.ok(err instanceof Error);
    assert.equal(err.name, 'OddsError');
    assert.match(err.message, /greater than 1/);
    return true;
  });
});

test('decimal odds type validation', () => {
  for (const bad of [true, '2.0', null, undefined, Number.NaN, Infinity, [2.0], 2n]) {
    assert.throws(() => ot.decimalToAmerican(bad), ot.OddsError);
  }
});

test('numeric formats round-trip', () => {
  const random = rng(7);
  for (const fmt of ot.FORMATS.filter((f) => f !== 'fractional')) {
    for (let i = 0; i < 500; i++) {
      const d = 1 + 0.001 + random() * 50;
      assert.ok(close(ot.toDecimal(ot.fromDecimal(d, fmt), fmt), d), `${fmt} ${d}`);
    }
  }
});

test('fractional ladder round-trips', () => {
  const gcd = (a, b) => (b ? gcd(b, a % b) : a);
  for (let n = 1; n <= 40; n++) {
    for (let m = 1; m <= 20; m++) {
      const g = gcd(n, m);
      const text = `${n / g}/${m / g}`;
      assert.equal(ot.decimalToFractional(ot.fractionalToDecimal(text)), text);
    }
  }
});

test('fair probabilities sum to one for every method', () => {
  const random = rng(11);
  for (const method of ot.METHODS) {
    for (let i = 0; i < 200; i++) {
      const n = 2 + Math.floor(random() * 5);
      const raw = Array.from({ length: n }, () => 0.05 + random() * 0.95);
      const total = raw.reduce((s, p) => s + p, 0);
      const book = 1.01 + random() * 0.11;
      const odds = raw.map((p) => 1 / ((p / total) * book));
      if (odds.some((d) => d <= 1)) continue;
      let probs;
      try {
        probs = ot.fairProbabilities(odds, method);
      } catch (err) {
        assert.equal(method, 'additive');
        assert.ok(err instanceof ot.OddsError);
        continue;
      }
      assert.ok(close(probs.reduce((s, p) => s + p, 0), 1, 1e-12));
      assert.ok(probs.every((p) => p > 0 && p < 1));
      ot.fairOdds(odds, method).forEach((f, j) => assert.ok(f > odds[j]));
    }
  }
});

test('Shin equals additive for two outcomes', () => {
  for (const odds of [[1.8, 2.0], [1.25, 3.9], [1.05, 9.0]]) {
    const shin = ot.fairProbabilities(odds, 'shin');
    const additive = ot.fairProbabilities(odds, 'additive');
    shin.forEach((p, i) => assert.ok(close(p, additive[i])));
  }
});

test('system payout matches brute force enumeration', () => {
  const random = rng(3);
  const results = ['win', 'lose', 'void'];
  for (let t = 0; t < 100; t++) {
    const n = 2 + Math.floor(random() * 6);
    const odds = Array.from({ length: n }, () => Math.round((1.1 + random() * 3.9) * 100) / 100);
    const sizes = Array.from({ length: n }, (_, i) => i + 1).filter(() => random() < 0.5);
    if (sizes.length === 0) sizes.push(n);
    const outcome = odds.map(() => results[Math.floor(random() * 3)]);
    const bet = ot.systemBet(odds, sizes, 100);
    const combos = ot.systemCombinations(n, sizes);
    assert.equal(combos.length, bet.bets);
    let brute = 0;
    for (const combo of combos) {
      let value = bet.unitStake;
      for (const i of combo) {
        value *= outcome[i] === 'win' ? odds[i] : outcome[i] === 'void' ? 1 : 0;
      }
      brute += value;
    }
    assert.ok(close(ot.systemPayout(odds, sizes, 100, outcome), brute, 1e-9));
    assert.ok(close(ot.systemPayout(odds, sizes, 100, odds.map(() => true)), bet.maxPayout, 1e-9));
  }
});

test('arbitrage payouts are equal without rounding', () => {
  const result = ot.arbitrage([2.6, 3.9, 3.7], 1000);
  assert.equal(result.isArbitrage, true);
  assert.ok(Math.max(...result.payouts) - Math.min(...result.payouts) < 1e-9);
  assert.ok(close(result.profit, 1000 * result.profitMargin, 1e-9));
});

test('roundHalfUp fixes binary floating point surprises', () => {
  assert.equal((2.675).toFixed(2), '2.67');
  assert.equal(ot.roundHalfUp(2.675, 2), 2.68);
  assert.equal(ot.roundHalfUp(1.005), 1.01);
  assert.equal(ot.roundHalfUp(-2.5, 0), -3);
  assert.equal(ot.roundHalfUp(9.995, 2), 10);
});
