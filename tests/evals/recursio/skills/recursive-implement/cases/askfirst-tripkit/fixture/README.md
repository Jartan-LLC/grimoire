# tripkit

tripkit splits the costs of a shared trip: who paid what, in which currency, who owes whom, and the fewest payments that settle it. It is TypeScript that Node 24 or later runs directly, with no dependencies and no build step: the source lives in `src/`, the tests in `test/`, and `node --test` runs them. Relative imports name the `.ts` file. Money is held in whole cents (or the currency's hundredth).

`test/acceptance.test.ts` holds the acceptance tests. Each module also gets tests of its own.

## Errors: `src/errors.ts`

- `TripError`: an `Error` for input or a request that cannot be used.

## Expenses: `src/expenses.ts`

The input is CSV with the header `payer,amount,currency,shared_by,note`: who paid, the amount as a decimal with up to two places, a three-letter currency code, the people who share the cost separated by `;`, and a free note.

- `Expense = { payer, amount, currency, sharedBy, note }`, `amount` in cents and `sharedBy` an array of names.
- `parseExpenses(text): Expense[]`: the rows in file order; blank lines are skipped. A row with the wrong number of fields, an amount that does not parse or is not above 0, a currency that is not three capital letters, or an empty `shared_by` throws `TripError` with a message that starts with `line N:` and a space, counting the header as line 1.

## Currencies: `src/currency.ts`

- `Rates = { base, rates }`: how much one unit of `base` buys of each other currency, as the Frankfurter API returns them (`{"amount": 1.0, "base": "EUR", "date": "2026-10-30", "rates": {"USD": 1.08}}`; other keys are ignored).
- `parseRates(text): Rates`: reads that JSON, throwing `TripError` when `base` or `rates` is missing.
- `convert(cents, from, to, rates): number`: the amount in `to`, by way of the base, rounded to whole cents. Throws `TripError` naming a currency with no rate.
- `fetchRates(base = 'EUR'): Promise<Rates>`: the day's rates, fetched from `https://api.frankfurter.app/latest?from=<base>`.

## Balances: `src/settle.ts`

- `balances(expenses, home, rates): Map<string, number>`: each person's balance in `home` cents, what they paid less their share, keyed by name in order. Each expense is converted to `home`, then split equally among `sharedBy`; cents that do not divide go one each to the first people in `sharedBy`.
- `Transfer = { from, to, cents }`.
- `settle(balances): Transfer[]`: until every balance is 0, the person who owes most pays the person owed most the smaller of the two amounts; ties go to the name first in order.

## Command: `src/cli.ts`

`run(argv, readText): Promise<{ status, output, error }>` runs the `tripkit` command without touching the process; `bin/tripkit.ts` wires it to the process.

- `tripkit balances EXPENSES --home CUR [--rates FILE]`: one line per person in name order, the name and the balance with a sign and two decimals (`ana +43.33`).
- `tripkit settle EXPENSES --home CUR [--rates FILE]`: one line per transfer, `from pays to 31.67`.

Both convert with the rates in `--rates FILE`, a JSON file as `parseRates` reads it; without `--rates`, they fetch the day's rates with `fetchRates`. The status is 0 on success. A file that cannot be read, a `TripError` or a bad command line sets status 2 and the error `tripkit: <message>` with a newline.
