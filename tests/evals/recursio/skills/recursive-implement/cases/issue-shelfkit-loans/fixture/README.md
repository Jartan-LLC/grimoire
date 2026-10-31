# shelfkit

shelfkit runs the loans desk of a small library: checkouts, returns, fines and the overdue report. Python 3.11 or later, standard library only. The package lives in `src/shelfkit/`, where `model.py` holds the data model.

`tests/test_acceptance.py` holds the acceptance tests. Each module also gets tests of its own.

## Data model: `shelfkit.model`

- `Book(isbn, title, price: Decimal)`, `Member(id, name, limit: int)` and `Loan(isbn, member, out: date, due: date, back: date | None = None)`: frozen dataclasses. `member` is a member's id.
- `Library(books: dict[str, Book], members: dict[str, Member], loans: list[Loan])`, kept as JSON by `load(path)` and `save(library, path)`.
- `LoanError(Exception)`: a loan that cannot be made or closed.

## Loans: `shelfkit.loans`

- `checkout(library, isbn, member, today, days=21) -> Loan`: adds a new loan to `library.loans` and returns it. `due` is `today` plus `days`, moved to the Monday after when it falls on a Sunday. Raises `LoanError` when the book or the member is unknown, the book is out (it has a loan with no `back`), or the member already has `limit` open loans.
- `return_book(library, isbn, today) -> Loan`: replaces the book's open loan with one whose `back` is `today`, and returns it. Raises `LoanError` when the book is not out.

## Fines: `shelfkit.fines`

- `days_late(loan, today) -> int`: the days from `due` to `back`, or to `today` while the loan is open; never below 0.
- `fine(loan, today) -> Decimal`: nothing for up to two days late; past that, 0.20 for every day late, the first two included.

## Overdue report: `shelfkit.report`

- `OverdueLine(member, title, due, days_late, fine)`: a frozen dataclass, `member` being the member's name.
- `overdue_report(library, today) -> list[OverdueLine]`: one line for each open loan past its due date, most days late first, then by title.

## Command: `shelfkit.cli`

`main(argv: list[str] | None = None) -> int`. Every subcommand takes the library file first, and `--today YYYY-MM-DD`, which defaults to the current date.

- `shelfkit checkout LIBRARY ISBN MEMBER`: records the loan, saves the library and prints `due YYYY-MM-DD`.
- `shelfkit return LIBRARY ISBN`: records the return, saves the library and prints the loan's fine as `fine 0.00`.
- `shelfkit overdue LIBRARY`: prints the overdue report, one tab-separated line per loan: the member's name, the title, the due date, the days late and the fine with two decimals.

A `LoanError` prints `shelfkit: <message>` to stderr and exits 1, leaving the library file as it was.
