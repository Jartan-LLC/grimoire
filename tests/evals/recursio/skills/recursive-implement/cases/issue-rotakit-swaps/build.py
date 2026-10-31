"""Build this case's history: run by the eval runner inside the fixture repository."""

import pathlib

PLAN = """# Plan: planning, swaps and the calendar export (#47)

## Approach

Build the three pieces the README describes on the existing model, each with its tests, then the
command that joins them.

## Steps

1. `src/rotakit/schedule.py`: `plan`, with `tests/test_schedule.py`.
2. `src/rotakit/swaps.py`: `swap` and `give`, with `tests/test_swaps.py`.
3. `src/rotakit/ical.py`: `to_ical`, with `tests/test_ical.py`.
4. `src/rotakit/cli.py`: the `plan`, `swap` and `export` subcommands, with `tests/test_cli.py`.
5. `src/rotakit/__main__.py`: run the command, so that `python -m rotakit` works where the
   `rotakit` script is not installed.

## Verification

- `python3 -m pytest -q`
- `python3 scripts/lint.py`
"""

target = pathlib.Path(".claude/workspace/issue-47/plan.md")
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(PLAN)
