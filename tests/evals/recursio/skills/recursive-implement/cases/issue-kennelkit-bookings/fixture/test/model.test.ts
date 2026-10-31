/** @file The kennel file and the date arithmetic. */
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { KennelError, addDays, formatKennel, parseKennel, weekday } from '../src/model.ts';

test('the kennel file round-trips', () => {
  const kennel = { runs: { small: 2, large: 1 }, dogs: [{ id: 'rex', name: 'Rex', size: 'large' as const, vaccinatedUntil: '2027-06-01' }], bookings: [] };
  assert.deepEqual(parseKennel(formatKennel(kennel)), kennel);
});

test('date arithmetic', () => {
  assert.equal(addDays('2026-12-31', 1), '2027-01-01');
  assert.equal(weekday('2026-12-25'), 5);
  assert.throws(() => addDays('2026-02-30', 1), KennelError);
});
