"""Build this case's history: run by the eval runner inside the fixture repository."""

import pathlib

PLAN = """# Plan: bookings, prices and occupancy (#18)

## Approach

Build the three pieces the README describes on the existing model, each with its tests, then the
command that joins them.

## Steps

1. `src/bookings.ts`: `book` and `cancel`, with `test/bookings.test.ts`.
2. `src/pricing.ts`: `PRICES` and `price`, with `test/pricing.test.ts`.
3. `src/occupancy.ts`: `occupancy` and `busiest`, with `test/occupancy.test.ts`.
4. `src/cli.ts`: the `book`, `cancel` and `occupancy` subcommands, with `test/cli.test.ts`.
5. `kennelkit occupancy` also takes `--json`, printing the nights as one JSON array of
   `{ date, small, large }`, so the website can show the free runs.

## Verification

- `node --test`
- `node scripts/lint.ts`
"""

target = pathlib.Path(".claude/workspace/issue-18/plan.md")
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(PLAN)
