// Copyright 2026 tripkit contributors. MIT licence.
// Acceptance tests for tripkit, as the README specifies.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { run } from '../src/cli.ts';
import { convert, parseRates } from '../src/currency.ts';
import { TripError } from '../src/errors.ts';
import { parseExpenses } from '../src/expenses.ts';
import { balances, settle } from '../src/settle.ts';

const EXPENSES = `payer,amount,currency,shared_by,note
ana,90.00,EUR,ana;ben;cy,dinner

ben,30,EUR,ben;cy,taxi
cy,54.00,USD,ana;ben;cy,museum
`;

const RATES = '{"amount": 1.0, "base": "EUR", "date": "2026-10-30", "rates": {"USD": 1.08, "GBP": 0.86}}';

const FILES: Record<string, string> = { 'trip.csv': EXPENSES, 'rates.json': RATES };

function read(path: string): string {
  if (!(path in FILES)) throw new Error(`ENOENT: ${path}`);
  return FILES[path];
}

test('expenses in cents', () => {
  const expenses = parseExpenses(EXPENSES);
  assert.equal(expenses.length, 3);
  assert.deepEqual(expenses[1], { payer: 'ben', amount: 3000, currency: 'EUR', sharedBy: ['ben', 'cy'], note: 'taxi' });
});

test('a bad expense names its line', () => {
  for (const row of ['ana,0,EUR,ana,x', 'ana,5,euro,ana,x', 'ana,5,EUR,,x', 'ana,5,EUR,ana']) {
    assert.throws(() => parseExpenses(`payer,amount,currency,shared_by,note\nben,1,EUR,ben,ok\n${row}\n`), (e: unknown) => e instanceof TripError && /^line 3: /.test(e.message), row);
  }
});

test('convert by way of the base', () => {
  const rates = parseRates(RATES);
  assert.equal(convert(5400, 'USD', 'EUR', rates), 5000);
  assert.equal(convert(1000, 'EUR', 'GBP', rates), 860);
  assert.equal(convert(860, 'GBP', 'USD', rates), 1080);
  assert.throws(() => convert(100, 'EUR', 'JPY', rates), (e: unknown) => e instanceof TripError && e.message.includes('JPY'));
});

test('balances share each cost, odd cents to the first people', () => {
  const result = balances(parseExpenses(EXPENSES), 'EUR', parseRates(RATES));
  assert.deepEqual([...result], [['ana', 4333], ['ben', -3167], ['cy', -1166]]);
});

test('settle: the biggest debtor pays the biggest creditor', () => {
  const owed = new Map([['ana', 4333], ['ben', -3167], ['cy', -1166]]);
  assert.deepEqual(settle(owed), [{ from: 'ben', to: 'ana', cents: 3167 }, { from: 'cy', to: 'ana', cents: 1166 }]);
  assert.deepEqual(settle(new Map([['ana', 0]])), []);
});

test('cli balances', async () => {
  assert.deepEqual(await run(['balances', 'trip.csv', '--home', 'EUR', '--rates', 'rates.json'], read), { status: 0, output: 'ana +43.33\nben -31.67\ncy -11.66\n', error: '' });
});

test('cli settle', async () => {
  assert.equal((await run(['settle', 'trip.csv', '--home', 'EUR', '--rates', 'rates.json'], read)).output, 'ben pays ana 31.67\ncy pays ana 11.66\n');
});

test('cli errors exit 2', async () => {
  const missing = await run(['settle', 'nope.csv', '--home', 'EUR', '--rates', 'rates.json'], read);
  assert.equal(missing.status, 2);
  assert.ok(missing.error.startsWith('tripkit: '));
  FILES['bad.csv'] = 'payer,amount,currency,shared_by,note\nana,-3,EUR,ana,x\n';
  const bad = await run(['balances', 'bad.csv', '--home', 'EUR', '--rates', 'rates.json'], read);
  assert.equal(bad.status, 2);
  assert.ok(bad.error.startsWith('tripkit: line 2: '), bad.error);
});
