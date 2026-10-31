# parkkit

parkkit prices the stays in a car park and reports how full it was. Node 20 or later, no dependencies; the source lives in `src/` as ES modules, the tests in `test/`, and `node --test` runs them. Times are local and written `YYYY-MM-DDTHH:MM`; money is held in whole cents.

`test/acceptance.test.js` holds the acceptance tests. Each module also gets tests of its own.

## Shared: `src/model.js`

- `ParkError`: an `Error` for bad input or a fee that cannot be worked out.
- `toMinutes(time)`: a time as whole minutes since 1970-01-01T00:00, throwing `ParkError` for a time that does not parse; `formatTime(minutes)` turns it back. `formatCents(cents)` writes cents as a decimal with two places.

## Tickets: `src/tickets.js`

The input is CSV with the header `plate,in,out`; `out` is empty while the car is still parked.

- `parseTickets(text)`: one `{ plate, entry, exit }` per row in file order, `exit` being null for an empty `out`; blank lines are skipped. A row with the wrong number of fields, an empty plate, a time that does not parse or an `out` before its `in` throws `ParkError` with a message that starts with `line N:` and a space, counting the header as line 1.

## Rates: `src/rates.js`

- `parseRates(text)`: the four `name = value` lines `first_hour`, `per_hour` and `daily_cap`, in currency units such as `3.00`, and `grace_minutes`, a whole number; blank lines and lines starting with `#` are skipped. Returns `{ firstHour, perHour, dailyCap, graceMinutes }`, money in cents. A missing or unknown name, or a value that does not parse, throws `ParkError` naming it.

## Fees: `src/fees.js`

- `fee(ticket, rates)`: a stay of up to `graceMinutes` is free. A longer stay pays `firstHour` for its first hour or part of it, then `perHour` for each further hour or part of one, and no more than `dailyCap` for each day of the stay. A ticket with no `exit` throws `ParkError`.
- What a day of the stay means for the cap has not been settled yet: each calendar day the stay touches, or each 24 hours from entry.
- `total(tickets, rates)`: the fees of every ticket with an `exit`, summed.

## Occupancy: `src/occupancy.js`

- `occupancy(tickets, time)`: how many cars are parked at `time`, counting a car from its entry up to, but not including, its exit; a car with no exit is still parked.
- `peak(tickets)`: `{ time, cars }`, the earliest entry time at which the most cars are parked.

## Command: `src/cli.js`

`run(argv, readText)` runs the `parkkit` command without touching the process and returns `{ status, output, error }`; `bin/parkkit.js` wires it to the process.

- `parkkit fees TICKETS RATES`: one line per ticket with an exit, in file order, `plate fee`, then `total fee`, fees with two decimals.
- `parkkit peak TICKETS`: `peak TIME N cars`.
- `parkkit at TICKETS TIME`: `N cars`.

The status is 0 on success. A file that cannot be read, a `ParkError` or a bad command line sets status 2 and the error `parkkit: <message>` with a newline.
