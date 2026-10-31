// @ts-check
// Tests for kelvin.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { run } from '../src/cli.js';
import { convert } from '../src/tempconv.js';

function near(got, want) {
  assert.ok(Math.abs(got - want) < 1e-9, `got ${got}, want ${want}`);
}

test('C to K', () => near(convert(0, 'C', 'K'), 273.15));
test('K to C', () => near(convert(300, 'K', 'C'), 26.85));
test('F to K', () => near(convert(212, 'F', 'K'), 373.15));
test('K to F', () => near(convert(0, 'K', 'F'), -459.67));

test('below 0 K', () => assert.throws(() => convert(-1, 'K', 'C'), /absolute zero/));
test('below absolute zero in Celsius', () => assert.throws(() => convert(-300, 'C', 'F'), /absolute zero/));

test('command', () => {
  assert.deepEqual(run(['--from', 'C', '--to', 'K', '26.85']), { status: 0, output: '300.0\n', error: '' });
});

test('command: below absolute zero exits 2', () => {
  const result = run(['--from', 'K', '--to', 'C', '--', '-5']);
  assert.equal(result.status, 2);
  assert.match(result.error, /^tempconv: .*absolute zero/);
});
