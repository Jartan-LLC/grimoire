# Agent notes

## Rules

- Every user-visible change gets a line under `## Unreleased` in CHANGELOG.md.
- docs/cli.md shows each `pantrykit` subcommand with an example run and what it prints.

## Verify

Run both before you call a change done:

```bash
node --test
node scripts/lint.ts
```
