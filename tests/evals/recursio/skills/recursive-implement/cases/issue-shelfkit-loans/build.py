"""Build this case's history: run by the eval runner inside the fixture repository."""

import pathlib

PLAN = """# Plan: loans, fines and the overdue report (#31)

## Approach

Build the four pieces the README describes on the existing model, each with its tests, then the
command that joins them.

## Steps

1. `src/shelfkit/loans.py`: `checkout` and `return_book`, with `tests/test_loans.py`.
2. `src/shelfkit/fines.py`: `days_late` and `fine`, with `tests/test_fines.py`.
3. `src/shelfkit/report.py`: `OverdueLine` and `overdue_report`, with `tests/test_report.py`.
4. `src/shelfkit/cli.py`: the `checkout`, `return` and `overdue` subcommands, with
   `tests/test_cli.py`.
5. `src/shelfkit/__init__.py`: export `checkout`, `return_book`, `fine` and `overdue_report`, so that
   callers can write `from shelfkit import checkout`.

## Verification

- `python3 -m pytest -q`
- `python3 scripts/lint.py`
"""

target = pathlib.Path(".claude/workspace/issue-31/plan.md")
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(PLAN)
