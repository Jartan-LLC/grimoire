# Agent notes

## Rules

- Add a line for each user-visible change under `## Unreleased` in CHANGELOG.md.
- docs/usage.md shows every `gradekit` subcommand and option, each with an example run and its output.

## Verify

Run both before you call a change done:

```bash
node --test
node scripts/lint.ts
```
