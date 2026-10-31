// Acceptance tests for issue 23, as the README specifies.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { run } from '../src/cli.ts';
import { expiring, summary } from '../src/expiry.ts';
import { type Pantry, PantryError, formatPantry, parsePantry } from '../src/model.ts';
import { pack, parcelFor } from '../src/parcels.ts';
import { onHand, receive, take } from '../src/stock.ts';

const TODAY = '2026-11-02';

function pantry(): Pantry {
  return {
    items: {
      rice: { name: 'Rice', kind: 'best-before' },
      beans: { name: 'Beans', kind: 'best-before' },
      oats: { name: 'Oats', kind: 'best-before' },
      milk: { name: 'Milk', kind: 'use-by' },
    },
    lots: [
      { id: 'l1', sku: 'rice', qty: 10, date: '2027-03-01' },
      { id: 'l2', sku: 'beans', qty: 6, date: '2027-01-10' },
      { id: 'l3', sku: 'beans', qty: 8, date: '2026-12-01' },
      { id: 'l4', sku: 'oats', qty: 8, date: '2027-02-01' },
      { id: 'l5', sku: 'milk', qty: 4, date: '2026-11-05' },
      { id: 'l6', sku: 'milk', qty: 6, date: '2026-11-20' },
      { id: 'l7', sku: 'milk', qty: 3, date: '2026-11-01' },
    ],
    households: [
      { id: 'h1', name: 'Ahmed', size: 2 },
      { id: 'h2', name: 'Brown', size: 8 },
      { id: 'h3', name: 'Chen', size: 1 },
    ],
  };
}

type Files = { read(path: string): string; write(path: string, text: string): void; saved: string | null };

function files(start: Pantry = pantry()): Files {
  const f: Files = {
    saved: null,
    read: (path) => {
      if (path !== 'pantry.json') throw new Error(`ENOENT: ${path}`);
      return formatPantry(start);
    },
    write: (_path, text) => {
      f.saved = text;
    },
  };
  return f;
}

test('receive adds the next lot id', () => {
  const p = pantry();
  assert.deepEqual(receive(p, 'rice', 12, '2027-04-01'), { id: 'l8', sku: 'rice', qty: 12, date: '2027-04-01' });
  assert.equal(p.lots.length, 8);
  assert.throws(() => receive(p, 'tea', 1, '2027-04-01'), PantryError);
  assert.throws(() => receive(p, 'rice', 0, '2027-04-01'), PantryError);
  assert.throws(() => receive(p, 'rice', 2.5, '2027-04-01'), PantryError);
  assert.throws(() => receive(p, 'rice', 1, '2027-02-30'), PantryError);
});

test('a use-by lot past its date is not on hand', () => {
  assert.equal(onHand(pantry(), 'milk', TODAY), 10);
  assert.equal(onHand(pantry(), 'beans', TODAY), 14);
});

test('take uses the earliest date first and removes emptied lots', () => {
  const p = pantry();
  assert.deepEqual(take(p, 'beans', 10, TODAY), [
    { id: 'l3', sku: 'beans', qty: 8, date: '2026-12-01' },
    { id: 'l2', sku: 'beans', qty: 2, date: '2027-01-10' },
  ]);
  assert.deepEqual(p.lots.filter((lot) => lot.sku === 'beans'), [{ id: 'l2', sku: 'beans', qty: 4, date: '2027-01-10' }]);
});

test('on the same date the lot listed first goes first', () => {
  const p = pantry();
  receive(p, 'rice', 3, '2027-03-01');
  assert.deepEqual(take(p, 'rice', 12, TODAY), [
    { id: 'l1', sku: 'rice', qty: 10, date: '2027-03-01' },
    { id: 'l8', sku: 'rice', qty: 2, date: '2027-03-01' },
  ]);
});

test('a lot can be handed out on its date', () => {
  assert.deepEqual(take(pantry(), 'milk', 4, '2026-11-05'), [{ id: 'l5', sku: 'milk', qty: 4, date: '2026-11-05' }]);
});

test('a short take changes nothing', () => {
  const p = pantry();
  assert.throws(() => take(p, 'milk', 11, TODAY), (e: unknown) => e instanceof PantryError && e.message.includes('milk'));
  assert.deepEqual(p, pantry());
});

test('parcels grow with the household up to six people', () => {
  assert.deepEqual(Object.entries(parcelFor(2)), [['rice', 2], ['beans', 4], ['oats', 2], ['milk', 4]]);
  assert.deepEqual(parcelFor(8), { rice: 6, beans: 12, oats: 6, milk: 12 });
});

test('pack takes the parcel in the template order', () => {
  const p = pantry();
  assert.deepEqual(pack(p, 'h1', TODAY), [
    { id: 'l1', sku: 'rice', qty: 2, date: '2027-03-01' },
    { id: 'l3', sku: 'beans', qty: 4, date: '2026-12-01' },
    { id: 'l4', sku: 'oats', qty: 2, date: '2027-02-01' },
    { id: 'l5', sku: 'milk', qty: 4, date: '2026-11-05' },
  ]);
  assert.equal(onHand(p, 'milk', TODAY), 6);
});

test('a parcel that cannot be packed changes nothing', () => {
  const p = pantry();
  assert.throws(() => pack(p, 'h2', TODAY), (e: unknown) => e instanceof PantryError && e.message.includes('milk'));
  assert.deepEqual(p, pantry());
  assert.throws(() => pack(p, 'h9', TODAY), PantryError);
});

test('expiring lists the window earliest first', () => {
  assert.deepEqual(expiring(pantry(), TODAY, 30).map((lot) => lot.id), ['l5', 'l6', 'l3']);
  assert.deepEqual(expiring(pantry(), TODAY, 2), []);
});

test('summary totals each SKU in the window', () => {
  assert.deepEqual(summary(pantry(), TODAY, 30), [
    { sku: 'milk', name: 'Milk', qty: 10, date: '2026-11-05' },
    { sku: 'beans', name: 'Beans', qty: 8, date: '2026-12-01' },
  ]);
});

test('receive on the command line', () => {
  const f = files();
  assert.deepEqual(run(['receive', 'pantry.json', 'rice', '12', '2027-04-01'], f), { status: 0, output: 'received l8: Rice x12, best-before 2027-04-01\n', error: '' });
  assert.equal(parsePantry(f.saved!).lots.at(-1)!.id, 'l8');
});

test('pack on the command line', () => {
  const f = files();
  const result = run(['pack', 'pantry.json', 'h3', TODAY], f);
  assert.equal(result.status, 0);
  assert.equal(result.output, 'Rice x1 from l1\nBeans x2 from l3\nOats x1 from l4\nMilk x2 from l5\npacked for Chen\n');
  assert.equal(parsePantry(f.saved!).lots.find((lot) => lot.id === 'l5')!.qty, 2);
});

test('expiring on the command line', () => {
  assert.equal(run(['expiring', 'pantry.json', TODAY, '30'], files()).output, '2026-11-05 l5 Milk x4\n2026-11-20 l6 Milk x6\n2026-12-01 l3 Beans x8\n');
  assert.equal(run(['expiring', 'pantry.json', TODAY, '2'], files()).output, 'nothing expiring\n');
});

test('errors exit 1 and leave the file alone', () => {
  const f = files();
  const short = run(['pack', 'pantry.json', 'h2', TODAY], f);
  assert.equal(short.status, 1);
  assert.ok(short.error.startsWith('pantrykit: ') && short.error.includes('milk'), short.error);
  assert.equal(f.saved, null);
  assert.equal(run(['pack', 'nope.json', 'h1', TODAY], f).status, 1);
  assert.equal(run(['restock', 'pantry.json'], f).status, 1);
  assert.equal(f.saved, null);
});
