// Runs the shared test vectors (also used by the Python package) against the ESM build.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

import * as lib from '../dist/esm/index.js';

const { tolerance, cases } = JSON.parse(
  readFileSync(new URL('../../test-vectors/vectors.json', import.meta.url), 'utf8'),
);

const SPECIAL = { NaN: Number.NaN, Infinity: Infinity, '-Infinity': -Infinity };
const camel = (name) => name.replace(/_([a-z])/g, (_, c) => c.toUpperCase());

function decode(value) {
  if (Array.isArray(value)) return value.map(decode);
  if (value !== null && typeof value === 'object' && Object.keys(value).join() === '$number') {
    return SPECIAL[value.$number];
  }
  return value;
}

function assertClose(actual, expected, path = 'result') {
  if (typeof expected === 'number') {
    assert.equal(typeof actual, 'number', `${path}: expected a number, got ${actual}`);
    const bound = tolerance * Math.max(1, Math.abs(expected));
    assert.ok(Math.abs(actual - expected) <= bound, `${path}: ${actual} !== ${expected}`);
  } else if (Array.isArray(expected)) {
    assert.ok(Array.isArray(actual), `${path}: expected an array, got ${actual}`);
    assert.equal(actual.length, expected.length, `${path}: length`);
    expected.forEach((e, i) => assertClose(actual[i], e, `${path}[${i}]`));
  } else if (expected !== null && typeof expected === 'object') {
    const keys = Object.keys(expected).map(camel).sort();
    assert.deepEqual(Object.keys(actual).sort(), keys, `${path}: keys`);
    for (const [key, e] of Object.entries(expected)) assertClose(actual[camel(key)], e, `${path}.${camel(key)}`);
  } else {
    assert.equal(actual, expected, path);
  }
}

for (const c of cases) {
  const name = camel(c.fn);
  test(`${name}(${JSON.stringify(c.args)})`.slice(0, 100), () => {
    const fn = lib[name];
    assert.equal(typeof fn, 'function', `${name} is not exported`);
    const args = decode(c.args);
    if (c.error) {
      assert.throws(() => fn(...args), lib.OddsError);
    } else {
      assertClose(fn(...args), c.expected);
    }
  });
}

test('every exported function has vectors', () => {
  const covered = new Set(cases.map((c) => camel(c.fn)));
  const exported = Object.entries(lib)
    .filter(([name, value]) => typeof value === 'function' && /^[a-z]/.test(name))
    .map(([name]) => name);
  assert.deepEqual(exported.filter((name) => !covered.has(name)), []);
});
