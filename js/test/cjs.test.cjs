// The CommonJS build must expose the same API as the ESM build.
const assert = require('node:assert/strict');
const { test } = require('node:test');

const cjs = require('odds-tools');

test('require() resolves to the CommonJS build', async () => {
  assert.ok(require.resolve('odds-tools').endsWith('dist/cjs/index.js'));
  const esm = await import('odds-tools');
  assert.deepEqual(Object.keys(cjs).sort(), Object.keys(esm).sort());
  assert.equal(cjs.decimalToFractional(2.5), '3/2');
  assert.equal(cjs.americanToDecimal(-200), 1.5);
  assert.throws(() => cjs.americanToDecimal(50), cjs.OddsError);
});
