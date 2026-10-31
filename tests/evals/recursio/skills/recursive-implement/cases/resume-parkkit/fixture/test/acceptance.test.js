// SPDX-License-Identifier: ISC
// Acceptance tests for parkkit, as the README specifies.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { run } from '../src/cli.js';
import { fee, total } from '../src/fees.js';
import { ParkError } from '../src/model.js';
import { occupancy, peak } from '../src/occupancy.js';
import { parseRates } from '../src/rates.js';
import { parseTickets } from '../src/tickets.js';

const TICKETS = `plate,in,out
AB12,2026-10-01T08:00,2026-10-01T08:10
CD34,2026-10-01T08:30,2026-10-01T10:15

EF56,2026-10-01T07:00,2026-10-01T19:30
GH78,2026-10-01T09:00,
`;

const RATES = '# weekday rates\nfirst_hour = 3.00\nper_hour = 2.00\ndaily_cap = 18.00\ngrace_minutes = 15\n';

const FILES = { 'tickets.csv': TICKETS, 'rates.txt': RATES };

function read(path) {
  if (!(path in FILES)) throw new Error(`ENOENT: ${path}`);
  return FILES[path];
}

const rates = () => parseRates(RATES);
const stay = (entry, exit) => ({ plate: 'X1', entry, exit });

test('tickets parse in file order', () => {
  const tickets = parseTickets(TICKETS);
  assert.equal(tickets.length, 4);
  assert.deepEqual(tickets[3], { plate: 'GH78', entry: '2026-10-01T09:00', exit: null });
});

test('an exit before its entry names the line', () => {
  assert.throws(() => parseTickets('plate,in,out\nAB12,2026-10-01T08:00,2026-10-01T07:59\n'), (e) => e instanceof ParkError && /^line 2: /.test(e.message));
});

test('rates in cents', () => {
  assert.deepEqual(rates(), { firstHour: 300, perHour: 200, dailyCap: 1800, graceMinutes: 15 });
  assert.throws(() => parseRates('first_hour = 3.00\nper_hour = 2.00\ngrace_minutes = 15\n'), (e) => e instanceof ParkError && e.message.includes('daily_cap'));
});

test('a stay within the grace period is free', () => {
  assert.equal(fee(stay('2026-10-01T08:00', '2026-10-01T08:15'), rates()), 0);
});

test('the first hour, then each started hour', () => {
  assert.equal(fee(stay('2026-10-01T08:00', '2026-10-01T09:00'), rates()), 300);
  assert.equal(fee(stay('2026-10-01T08:00', '2026-10-01T09:01'), rates()), 500);
  assert.equal(fee(stay('2026-10-01T08:30', '2026-10-01T10:15'), rates()), 500);
});

test('a long day stops at the cap', () => {
  assert.equal(fee(stay('2026-10-01T07:00', '2026-10-01T19:30'), rates()), 1800);
});

test('a ticket still open has no fee yet', () => {
  assert.throws(() => fee(stay('2026-10-01T09:00', null), rates()), ParkError);
});

test('total skips open tickets', () => {
  assert.equal(total(parseTickets(TICKETS), rates()), 2300);
});

test('occupancy counts from entry up to exit', () => {
  const tickets = parseTickets(TICKETS);
  assert.equal(occupancy(tickets, '2026-10-01T08:05'), 2);
  assert.equal(occupancy(tickets, '2026-10-01T08:10'), 1);
  assert.equal(occupancy(tickets, '2026-10-01T09:30'), 3);
});

test('peak is the earliest busiest entry', () => {
  assert.deepEqual(peak(parseTickets(TICKETS)), { time: '2026-10-01T09:00', cars: 3 });
});

test('cli fees', () => {
  assert.deepEqual(run(['fees', 'tickets.csv', 'rates.txt'], read), { status: 0, output: 'AB12 0.00\nCD34 5.00\nEF56 18.00\ntotal 23.00\n', error: '' });
});

test('cli peak and at', () => {
  assert.equal(run(['peak', 'tickets.csv'], read).output, 'peak 2026-10-01T09:00 3 cars\n');
  assert.equal(run(['at', 'tickets.csv', '2026-10-01T08:05'], read).output, '2 cars\n');
});

test('cli errors exit 2', () => {
  const missing = run(['fees', 'nope.csv', 'rates.txt'], read);
  assert.equal(missing.status, 2);
  assert.ok(missing.error.startsWith('parkkit: '));
  FILES['bad.csv'] = 'plate,in,out\n,2026-10-01T08:00,\n';
  const bad = run(['peak', 'bad.csv'], read);
  assert.equal(bad.status, 2);
  assert.ok(bad.error.startsWith('parkkit: line 2: '), bad.error);
});
