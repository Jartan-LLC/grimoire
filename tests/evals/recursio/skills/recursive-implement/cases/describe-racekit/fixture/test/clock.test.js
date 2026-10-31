import assert from 'node:assert/strict';
import { test } from 'node:test';
import { RaceError, formatDuration, parseClock } from '../src/clock.js';

test('clock times', () => {
  assert.equal(parseClock('09:00:04'), 32404);
  assert.throws(() => parseClock('9:00'), RaceError);
  assert.throws(() => parseClock('09:61:00'), RaceError);
});

test('durations', () => {
  assert.equal(formatDuration(2467), '0:41:07');
  assert.equal(formatDuration(3725), '1:02:05');
});
