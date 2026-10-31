"""Build this case's history: run by the eval runner inside the fixture repository.

A walk-away run that stopped after its first wave: the shared module, both wave 1 parts with their
tests, and split.md recording wave 1 passed and waves 2 and 3 pending, all left uncommitted.
"""

import pathlib

FILES = {
    "src/model.js": r"""// SPDX-License-Identifier: ISC
// Shared pieces for parkkit: the error type, time arithmetic and money formatting.

export class ParkError extends Error {}

const TIME = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/;

export function toMinutes(time) {
  const match = TIME.exec(time ?? '');
  if (!match) throw new ParkError(`bad time ${JSON.stringify(time)}`);
  const [year, month, day, hour, minute] = match.slice(1).map(Number);
  const ms = Date.UTC(year, month - 1, day, hour, minute);
  if (new Date(ms).toISOString().slice(0, 16) !== time) throw new ParkError(`bad time ${JSON.stringify(time)}`);
  return ms / 60000;
}

export function formatTime(minutes) {
  return new Date(minutes * 60000).toISOString().slice(0, 16);
}

export function formatCents(cents) {
  return (cents / 100).toFixed(2);
}
""",
    "src/tickets.js": r"""// SPDX-License-Identifier: ISC
// Parse a tickets file.
import { ParkError, toMinutes } from './model.js';

export function parseTickets(text) {
  const tickets = [];
  text.split('\n').forEach((raw, index) => {
    const line = raw.trim();
    if (index === 0 || line === '') return;
    const where = `line ${index + 1}: `;
    const fields = line.split(',').map((field) => field.trim());
    if (fields.length !== 3) throw new ParkError(`${where}expected plate,in,out`);
    const [plate, entry, out] = fields;
    if (plate === '') throw new ParkError(`${where}empty plate`);
    const exit = out === '' ? null : out;
    try {
      toMinutes(entry);
      if (exit !== null && toMinutes(exit) < toMinutes(entry)) throw new ParkError('out is before in');
    } catch (error) {
      throw new ParkError(`${where}${error.message}`);
    }
    tickets.push({ plate, entry, exit });
  });
  return tickets;
}
""",
    "src/rates.js": r"""// SPDX-License-Identifier: ISC
// Parse a rates file into cents and minutes.
import { ParkError } from './model.js';

const MONEY = { first_hour: 'firstHour', per_hour: 'perHour', daily_cap: 'dailyCap' };

export function parseRates(text) {
  const rates = {};
  for (const raw of text.split('\n')) {
    const line = raw.trim();
    if (line === '' || line.startsWith('#')) continue;
    const [name, value] = line.split('=').map((part) => part.trim());
    if (name in MONEY) {
      if (!/^\d+(\.\d{1,2})?$/.test(value ?? '')) throw new ParkError(`${name}: bad amount ${value}`);
      rates[MONEY[name]] = Math.round(Number(value) * 100);
    } else if (name === 'grace_minutes') {
      if (!/^\d+$/.test(value ?? '')) throw new ParkError(`grace_minutes: bad number ${value}`);
      rates.graceMinutes = Number(value);
    } else {
      throw new ParkError(`unknown rate ${name}`);
    }
  }
  for (const [name, key] of [...Object.entries(MONEY), ['grace_minutes', 'graceMinutes']]) {
    if (!(key in rates)) throw new ParkError(`missing rate ${name}`);
  }
  return { firstHour: rates.firstHour, perHour: rates.perHour, dailyCap: rates.dailyCap, graceMinutes: rates.graceMinutes };
}
""",
    "test/tickets.test.js": r"""// SPDX-License-Identifier: ISC
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { ParkError } from '../src/model.js';
import { parseTickets } from '../src/tickets.js';

test('an empty out is still parked', () => {
  assert.deepEqual(parseTickets('plate,in,out\n\nAB12,2026-10-01T08:00,\n'), [{ plate: 'AB12', entry: '2026-10-01T08:00', exit: null }]);
});

for (const [row, why] of [
  ['AB12,2026-10-01T08:00', 'too few fields'],
  [',2026-10-01T08:00,', 'empty plate'],
  ['AB12,2026-13-01T08:00,', 'bad month'],
  ['AB12,2026-10-01T08:00,2026-10-01T07:00', 'out before in'],
]) {
  test(`a bad row names its line: ${why}`, () => {
    assert.throws(() => parseTickets(`plate,in,out\nCD34,2026-10-01T08:00,\n${row}\n`), (e) => e instanceof ParkError && /^line 3: /.test(e.message));
  });
}
""",
    "test/rates.test.js": r"""// SPDX-License-Identifier: ISC
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { ParkError } from '../src/model.js';
import { parseRates } from '../src/rates.js';

const GOOD = 'first_hour = 3.50\nper_hour = 2\ndaily_cap = 20.00\ngrace_minutes = 10\n';

test('money in cents, grace in minutes', () => {
  assert.deepEqual(parseRates(GOOD), { firstHour: 350, perHour: 200, dailyCap: 2000, graceMinutes: 10 });
});

test('unknown, missing and bad rates are errors', () => {
  assert.throws(() => parseRates(`${GOOD}night = 1.00\n`), (e) => e instanceof ParkError && e.message.includes('night'));
  assert.throws(() => parseRates('first_hour = 3.50\n'), ParkError);
  assert.throws(() => parseRates(GOOD.replace('2\n', 'two\n')), (e) => e.message.includes('per_hour'));
});
""",
    ".claude/workspace/parkkit/split.md": r"""If the splitting skill was lost to compaction, load `recursio:splitting-implementation` again and resume from the status lines below.

# Split: parkkit

## Settled decisions

- Shared module `src/model.js`: `ParkError`, `toMinutes`, `formatTime` and `formatCents` -- source: the README.
- Each module's own tests in `test/<module>.test.js`, run with `node --test test/<module>.test.js` -- source: decided here.
- Fees are whole cents throughout; nothing is rounded until `formatCents` -- source: the README.

## Wave 1

Snapshot before spawning: no changed files; contract hashes: src/model.js 0b88a8ed9ef413e1212e42ef094d4efb4f2ecc4a

### tickets

- Owns: src/tickets.js, test/tickets.test.js
- Depends on: src/model.js
- Contract: src/model.js
- Contract tests: test/acceptance.test.js, run with `node --test --test-name-pattern=ticket test/acceptance.test.js`
- Agent type: general-purpose
- Status: passed
- Outcome: built

### rates

- Owns: src/rates.js, test/rates.test.js
- Depends on: src/model.js
- Contract: src/model.js
- Contract tests: test/acceptance.test.js, run with `node --test --test-name-pattern=rates test/acceptance.test.js`
- Agent type: general-purpose
- Status: passed
- Outcome: built

### Barrier

Scope: every changed file lies in one part's scope; model.js matches its hash. `node --test test/tickets.test.js test/rates.test.js`: 7 passed. The acceptance tests: not run, as they import modules of later waves. No divergence; no retries.

## Wave 2

### fees

- Owns: src/fees.js, test/fees.test.js
- Depends on: src/model.js
- Contract: src/model.js, the README's Fees section
- Contract tests: test/acceptance.test.js, run with `node --test --test-name-pattern="stay|hour|cap|fee|total" test/acceptance.test.js`
- Agent type: general-purpose
- Status: pending
- Outcome:

### occupancy

- Owns: src/occupancy.js, test/occupancy.test.js
- Depends on: src/model.js
- Contract: src/model.js, the README's Occupancy section
- Contract tests: test/acceptance.test.js, run with `node --test --test-name-pattern="occupancy|peak" test/acceptance.test.js`
- Agent type: general-purpose
- Status: pending
- Outcome:

### Barrier

Not run yet.

## Wave 3

### cli

- Owns: src/cli.js, test/cli.test.js
- Depends on: tickets, rates, fees, occupancy
- Contract: the README's Command section
- Contract tests: test/acceptance.test.js, run with `node --test --test-name-pattern=cli test/acceptance.test.js`
- Agent type: general-purpose
- Status: pending
- Outcome:

### Barrier

Not run yet.

## Decided without asking

- Fees stay in whole cents until printed -- the README holds money in cents but does not say when to round.

## Left for the user
""",
}

for name, text in FILES.items():
    target = pathlib.Path(name)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
