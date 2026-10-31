# shiftboard

Plans and checks the staff rota of a care home -- who works when, what they are paid for it, and
how much leave they have left -- as a library and a command. Plain Node, no dependencies.

## Data model

`src/model.js` holds the records the modules pass to one another: `employee()`, `shift()` and
`leave()` build frozen records, `Role` and `LeaveKind` list the allowed values, `parseStamp()`,
`parseDay()` and `formatDay()` turn times and dates into numbers and back, and `RotaError` is the
error. Every module below works on these and nothing else of its siblings, except the command,
which uses them all. Bad input or a refused request throws `RotaError` with a message naming the
record or value at fault.

Times are wall-clock `YYYY-MM-DDTHH:MM` with no time zone; dates are `YYYY-MM-DD`. Money is whole
cents; "rounded" means rounded half up to a whole cent. A week runs Monday to Sunday, and a shift
belongs to the day and the week it starts in.

## Rota checks (`src/rota.js`)

- `check(shifts, employees)` returns a problem `{ shift, kind, detail }` per fault, `shift` being
  the 0-based index in the input list, ordered by `shift` and then by the kinds' order here:
  - `times`: the shift does not end after it starts. Such a shift gets no other check below.
  - `unknown`: no employee has the shift's `employee` id. Such a shift gets no other check below.
  - `role`: the shift's role is not the employee's. The detail is `nurse on a carer shift`.
  - `length`: the shift is longer than 12 hours.
  - `overlap`: taking each employee's shifts by start time, the shift starts before the
    previous one ends.
  - `rest`: the shift starts less than 11 hours after the previous one ends, when it does not
    overlap it. The detail is `rest of N h`, N the hours between, to one decimal place.
  - `weekly`: the shift takes the employee's hours in its week past 48. Only that shift is
    flagged, once per week; the detail is `N h in the week of DATE`, N the week's total hours to
    one decimal place and DATE its Monday.
- `cover(shifts, day, needs)` takes `needs`, an object of role to the number of staff that role
  needs every hour, and returns `{ hour, role, have, need }` for each hour from 0 to 23 of `day`
  where fewer shifts of that role cover the hour than it needs, ordered by hour and then role
  name. A shift covers an hour when it runs over the whole of it, whichever day it started on.

## Pay (`src/pay.js`)

- `PREMIUMS`: a night minute (from 22:00 to 06:00) earns 25 % on top of the base rate, a weekend
  minute (on a Saturday or Sunday) 50 %, and a minute on one of the `holidays` (a `Set` of
  `YYYY-MM-DD` dates) 100 %. Premiums do not add up: a minute earns only the highest it qualifies
  for. A minute belongs to the calendar day it falls on, not the day its shift started.
- `shiftPay(shift, employee, holidays = new Set())`: each minute of the shift at the base rate
  plus its premium, summed exactly and then rounded.
- `overtime(shifts, employee)`: the hours each week over the employee's `contractHours`, counting
  only that employee's shifts, earn half the base rate again (premiums aside), rounded per week.
- `payslip(shifts, employee, from, to, holidays = new Set())` returns
  `{ minutes, gross, overtime, total }` for the employee's shifts that start from `from` to `to`
  inclusive: their minutes, the sum of their `shiftPay`, their `overtime`, and the two added.

## Leave (`src/leave.js`)

Leave balances are in minutes. A working day of leave is a fifth of the employee's contract hours.

- `entitlement(employee, year)`: 5.6 weeks of contract hours, rounded to a whole minute; for an
  employee who started during `year`, that times the days from the start date to 31 December
  (both included) over the days in the year, rounded once at the end. An employee who starts after
  `year` is entitled to 0.
- `taken(leaves, employee, year)`: the employee's annual leave falling in `year`: each Monday to
  Friday from `from` to `to` counts one working day; weekends and days outside the year do not.
- `request(leaves, employee, wanted, year)` returns a new list with `wanted` added at the end. It
  is refused when `to` is before `from`, when the leave is not the employee's, when it overlaps
  any day of their other leave, or when it is annual leave and `taken` with it would pass
  `entitlement` for `year`.
- `bradford(leaves, employee, today)`: the Bradford factor of the employee's sick leave in the 365
  days up to and including `today`: S x S x D, S the number of spells and D their calendar days,
  counting only the days inside that window. A spell ending after `today` counts up to `today`.

## Command (`src/cli.js`)

Files are CSV with a header row:

- employees: `id,name,role,contract_hours,hourly_cents,start_date`
- shifts: `employee,start,end,role`
- leave: `employee,from,to,kind`

`--holidays FILE` names a file of holiday dates, one per line.

`main(argv, io = { out: process.stdout, err: process.stderr })` writes through `io.out.write()`
and `io.err.write()` and returns the exit status:

- `shiftboard check EMPLOYEES SHIFTS` prints `shift N: kind: detail` per problem, N counting from
  1; exit 1 when there is any.
- `shiftboard pay EMPLOYEES SHIFTS --employee ID --from DATE --to DATE [--holidays FILE]` prints
  `minutes N`, then `gross`, `overtime` and `total`, each as `name X.YY` in currency units.
- `shiftboard leave EMPLOYEES LEAVE --employee ID --year YEAR` prints `entitlement`, `taken` and
  `balance` (entitlement less taken), each as `name H.HH` in hours.

Bad input writes the error to `io.err` and exits 2; otherwise the exit status is 0.

## Usage

_To be written as each module lands: a short example per module and per subcommand._
