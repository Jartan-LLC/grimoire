"""Build this case's history: run by the eval runner inside the fixture repository."""

import pathlib

PLAN = """# Plan: stock, parcels and expiry (#23)

## Approach

Build the three pieces the README describes on the existing model, each with its tests, then the
command that joins them.

## Steps

1. `src/stock.ts`: `receive`, `onHand` and `take`, with `test/stock.test.ts`.
2. `src/parcels.ts`: `TEMPLATE`, `parcelFor` and `pack`, with `test/parcels.test.ts`.
3. `src/expiry.ts`: `expiring` and `summary`, with `test/expiry.test.ts`.
4. `src/cli.ts`: the `receive`, `pack` and `expiring` subcommands, with `test/cli.test.ts`.
5. `pantrykit pack` also takes `--dry-run`: it prints the same lines and leaves the pantry file as
   it was, so a volunteer can check a parcel before packing it.

## Verification

- `node --test`
- `node scripts/lint.ts`
"""

target = pathlib.Path(".claude/workspace/issue-23/plan.md")
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(PLAN)
