/** @file Acceptance tests for issue 18, as the README specifies. */
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { book, cancel } from '../src/bookings.ts';
import { run } from '../src/cli.ts';
import { type Kennel, KennelError, formatKennel, parseKennel } from '../src/model.ts';
import { busiest, occupancy } from '../src/occupancy.ts';
import { price } from '../src/pricing.ts';

function kennel(): Kennel {
  return {
    runs: { small: 2, large: 1 },
    dogs: [
      { id: 'rex', name: 'Rex', size: 'large', vaccinatedUntil: '2027-06-01' },
      { id: 'max', name: 'Max', size: 'large', vaccinatedUntil: '2027-03-01' },
      { id: 'pip', name: 'Pip', size: 'small', vaccinatedUntil: '2027-08-15' },
    ],
    bookings: [{ id: 'b1', dog: 'max', from: '2026-12-18', to: '2026-12-21' }],
  };
}

const rex = kennel().dogs[0];
const pip = kennel().dogs[2];

test('book adds the next id', () => {
  const k = kennel();
  assert.deepEqual(book(k, 'rex', '2026-12-21', '2026-12-28'), { id: 'b2', dog: 'rex', from: '2026-12-21', to: '2026-12-28' });
  assert.equal(k.bookings.length, 2);
});

test('book refuses a night with no run free, an unknown dog and a bad range', () => {
  for (const [dog, from, to] of [['rex', '2026-12-20', '2026-12-22'], ['fido', '2026-12-21', '2026-12-22'], ['rex', '2026-12-22', '2026-12-22']]) {
    assert.throws(() => book(kennel(), dog, from, to), KennelError, `${dog} ${from} ${to}`);
  }
});

test('book refuses a dog booked twice', () => {
  const k = kennel();
  book(k, 'pip', '2026-12-18', '2026-12-20');
  assert.throws(() => book(k, 'pip', '2026-12-19', '2026-12-21'), KennelError);
});

test('cancel removes a booking', () => {
  const k = kennel();
  assert.equal(cancel(k, 'b1').dog, 'max');
  assert.equal(k.bookings.length, 0);
  assert.throws(() => cancel(k, 'b9'), KennelError);
});

test('prices add the weekend and take 10% off a week', () => {
  assert.equal(price({ id: 'b2', dog: 'pip', from: '2026-12-18', to: '2026-12-20' }, pip), 7000);
  assert.equal(price({ id: 'b3', dog: 'rex', from: '2026-12-21', to: '2026-12-28' }, rex), 26100);
  assert.equal(price({ id: 'b4', dog: 'rex', from: '2026-12-21', to: '2026-12-22' }, rex, { small: 1000, large: 1500 }), 1500);
});

test('occupancy counts the runs taken each night', () => {
  const k = kennel();
  book(k, 'pip', '2026-12-20', '2026-12-22');
  assert.deepEqual(occupancy(k, '2026-12-19', '2026-12-22'), [
    { date: '2026-12-19', small: 0, large: 1 },
    { date: '2026-12-20', small: 1, large: 1 },
    { date: '2026-12-21', small: 1, large: 0 },
  ]);
  assert.deepEqual(busiest(k, '2026-12-19', '2026-12-22'), { date: '2026-12-20', small: 1, large: 1 });
  assert.equal(busiest(k, '2027-01-04', '2027-01-06'), null);
});

function desk(text: string) {
  const files = { 'kennel.json': text };
  return { files, io: { read: (path: string) => { if (!(path in files)) throw new Error(`ENOENT: ${path}`); return files[path as 'kennel.json']; }, write: (path: string, t: string) => { files[path as 'kennel.json'] = t; } } };
}

test('cli book saves and prints the price', () => {
  const { files, io } = desk(formatKennel(kennel()));
  assert.deepEqual(run(['book', 'kennel.json', 'rex', '2026-12-21', '2026-12-28'], io), { status: 0, output: 'booked b2: Rex 2026-12-21 to 2026-12-28, 261.00\n', error: '' });
  assert.equal(parseKennel(files['kennel.json']).bookings.length, 2);
});

test('cli cancel and occupancy', () => {
  const { files, io } = desk(formatKennel(kennel()));
  assert.equal(run(['occupancy', 'kennel.json', '2026-12-20', '2026-12-22'], io).output, '2026-12-20 small 0/2 large 1/1\n2026-12-21 small 0/2 large 0/1\n');
  assert.equal(run(['cancel', 'kennel.json', 'b1'], io).output, 'cancelled b1\n');
  assert.equal(parseKennel(files['kennel.json']).bookings.length, 0);
});

test('cli errors leave the file as it was', () => {
  const before = formatKennel(kennel());
  const { files, io } = desk(before);
  const result = run(['book', 'kennel.json', 'rex', '2026-12-20', '2026-12-22'], io);
  assert.equal(result.status, 1);
  assert.ok(result.error.startsWith('kennelkit: '));
  assert.equal(files['kennel.json'], before);
  assert.equal(run(['occupancy', 'missing.json', '2026-12-20', '2026-12-22'], io).status, 1);
});
