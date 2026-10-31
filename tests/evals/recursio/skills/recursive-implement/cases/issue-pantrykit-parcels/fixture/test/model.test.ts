// The pantry file and the date arithmetic.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { PantryError, addDays, checkDate, formatPantry, parsePantry } from '../src/model.ts';

test('the pantry file round-trips', () => {
  const pantry = {
    items: { rice: { name: 'Rice', kind: 'best-before' as const } },
    lots: [{ id: 'l1', sku: 'rice', qty: 4, date: '2027-03-01' }],
    households: [{ id: 'h1', name: 'Ahmed', size: 2 }],
  };
  assert.deepEqual(parsePantry(formatPantry(pantry)), pantry);
});

test('date arithmetic', () => {
  assert.equal(addDays('2026-12-31', 1), '2027-01-01');
  assert.equal(addDays('2026-11-02', 30), '2026-12-02');
  assert.equal(checkDate('2028-02-29'), '2028-02-29');
  assert.throws(() => checkDate('2026-02-30'), PantryError);
});
