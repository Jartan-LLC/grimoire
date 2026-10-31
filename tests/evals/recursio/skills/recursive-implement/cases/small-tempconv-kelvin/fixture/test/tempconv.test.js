// @ts-check
// Tests for Celsius and Fahrenheit.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { run } from '../src/cli.js';
import { convert, formatTemp } from '../src/tempconv.js';

test('C to F', () => assert.equal(formatTemp(convert(100, 'C', 'F')), '212.0'));
test('C to F with decimals', () => assert.equal(formatTemp(convert(21.5, 'C', 'F')), '70.7'));
test('F to C', () => assert.equal(formatTemp(convert(-40, 'F', 'C')), '-40.0'));
test('same unit', () => assert.equal(formatTemp(convert(12, 'C', 'C')), '12.0'));
test('unknown unit', () => assert.throws(() => convert(1, 'X', 'C'), /unknown unit X/));

test('command', () => {
  assert.deepEqual(run(['--from', 'C', '--to', 'F', '21.5']), { status: 0, output: '70.7\n', error: '' });
});

test('command: unknown unit exits 2', () => {
  assert.deepEqual(run(['--from', 'R', '--to', 'C', '5']), { status: 2, output: '', error: 'tempconv: unknown unit R\n' });
});
