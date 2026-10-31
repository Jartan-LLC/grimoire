import assert from 'node:assert/strict';
import { test } from 'node:test';
import { formatPercent } from '../src/format.ts';

test('one decimal', () => {
  assert.equal(formatPercent(85), '85.0');
  assert.equal(formatPercent(64.333), '64.3');
});
