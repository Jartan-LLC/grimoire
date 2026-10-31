# libcirc

Circulation for a small public library: lending and renewing items, overdue fines, and the holds
queue, as a library and a command.

## Data model

`src/libcirc/model.py` holds the records the modules pass to one another: `Item` and `ItemKind`,
`Patron` and `PatronKind`, `Loan`, `Hold`, `Payment` and `CircError`. Every module below works on
these and nothing else of its siblings, except the command, which uses them all. A refused
request or bad input raises `CircError` with a message saying why. Money is `decimal.Decimal`;
"rounded" means rounded half up to cents.

The library is open every day but Sunday, except on the closure days the caller passes in as
`closures` (a collection of dates; empty by default). An "open day" is a day it is open.

## Loans (`libcirc.loans`)

- `LOAN_DAYS`: 21 days for a book, 7 for a DVD. Reference items do not leave the building.
- `due_date(item, out, closures=())`: `out` plus the item's loan days, moved forward to the next
  open day when that day is not one. A reference item is an error.
- `checkout(item, patron, today, loans, closures=())` returns the new `Loan`. It is refused when
  the item is already out (an unreturned loan of its barcode), when the patron has an overdue
  loan (unreturned and due before `today`), or when the patron already has their limit of
  unreturned loans: 5 on a child's card, 15 on an adult's.
- `renew(loan, item, today, holds, closures=())` returns the loan with a new due date,
  `due_date(item, today)`, and one more renewal. It is refused for a returned loan, after 2
  renewals, when someone holds the barcode, or when the loan is more than 14 days overdue.
- `overdue(loans, today)`: the unreturned loans due before `today`, by due date and then barcode.

## Fines (`libcirc.fines`)

- `RATES`: 0.25 a day for a book, 1.00 for a DVD. `CAPS`: at most 5.00 for a book, 10.00 for a
  DVD, per loan.
- `overdue_days(loan, until, closures=())`: the open days after `loan.due`, up to and including
  the day it was returned, or `until` while it is still out.
- `fine(loan, item, patron, until, closures=())`: the first overdue open day is free; each one
  after it costs the item's rate, up to its cap. A child pays half, rounded, after the cap.
- `account(patron, loans, items, payments, today, closures=())` returns an `Account` (defined in
  this module: `owed`, `paid`, `balance`, `blocked`) for the patron: `owed` is the fines on all
  their loans as of `today`, `paid` the sum of their payments, `balance` the difference, and
  `blocked` is True when the balance is 10.00 or more.

## Holds (`libcirc.holds`)

- `place(holds, barcode, patron, when, loans)` returns a new list with the hold added at the
  end. It is refused when the patron already holds that barcode, has it out on loan, or already
  has 10 holds.
- `queue(holds, barcode)`: the barcode's holds by `placed`, earliest first.
- `on_return(holds, barcode, today, closures=())` returns `(pickup, holds)`. The first hold in
  the barcode's queue leaves the list and becomes a `Pickup` (defined in this module: `patron`,
  `barcode`, `expires`), where `expires` is the 7th open day after `today`. With no hold, the
  pickup is None and the list is unchanged.
- `expire(pickup, holds, today, closures=())` returns `(pickup, holds)`: once `today` is after
  `pickup.expires`, the item goes to the next hold, as `on_return` from `today` would give it;
  before that, the same pickup and list.

## Command (`libcirc.cli`)

Files are CSV with a header row:

- items: `barcode,title,kind`
- patrons: `id,name,kind`
- loans: `barcode,patron,out,due,returned,renewals`, `returned` empty while out
- holds: `barcode,patron,placed`, `placed` an ISO 8601 datetime
- payments: `patron,day,amount`

`--closures FILE` names a file of closure days, one ISO date per line.

`main(argv=None)` returns the exit status:

- `libcirc overdue ITEMS LOANS --today DATE [--closures FILE]` prints `barcode patron due days`
  per overdue loan, `days` being its overdue open days.
- `libcirc account ITEMS PATRONS LOANS PAYMENTS --patron ID --today DATE [--closures FILE]`
  prints `owed X`, `paid X` and `balance X`, then `blocked` or `ok`; exit 1 when blocked.
- `libcirc queue HOLDS --barcode BARCODE` prints the patrons in the barcode's queue, one per line.

Bad input prints the error on stderr and exits 2; otherwise the exit status is 0.

## Usage

_To be written as each module lands: a short example per module and per subcommand._
