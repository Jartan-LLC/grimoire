# Agent notes

## Rules

- Never rename or remove an existing command-line option without asking the maintainer first: people's scripts and cron jobs call them.
- Add a line for each user-visible change under `## Unreleased` in CHANGELOG.md.
- docs/reference.md lists every subcommand of `plantkit` with its options.

## Verify

Run both before you call a change done:

```bash
python3 -m pytest -q
python3 scripts/lint.py
```
