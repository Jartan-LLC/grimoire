"""Build this case's history: run by the eval runner inside the fixture repository."""

import pathlib

PLAN = """\
# Plan: libcirc circulation (#52)

## Steps

1. `src/libcirc/loans.py`: `LOAN_DAYS`, `due_date()`, `checkout()` with its three refusals,
   `renew()` with its four refusals, and `overdue()`, with `tests/test_loans.py`.
2. `src/libcirc/fines.py`: `RATES`, `CAPS`, `overdue_days()` over open days, `fine()` with the
   free first day, the caps and the child half rate, and `account()`, with `tests/test_fines.py`.
3. `src/libcirc/holds.py`: `place()` with its refusals, `queue()`, `on_return()` and `expire()`
   with the 7-open-day pickup window, with `tests/test_holds.py`.
4. `src/libcirc/cli.py`: the CSV readers, `--closures`, and the `overdue`, `account` and `queue`
   subcommands with their exit statuses, with `tests/test_cli.py`.
5. README: an example per module and per subcommand in the Usage section.

## Verification

- `python3 -m pytest -q`, the planted tests in `tests/planted/` included.
"""

plan = pathlib.Path(".claude/workspace/issue-52/plan.md")
plan.parent.mkdir(parents=True)
plan.write_text(PLAN)
