# Agent notes

## Rules

- notekit runs on the standard library alone. Ask the maintainer before adding any dependency.
- Add a line for each user-visible change under `## Unreleased` in CHANGELOG.md.
- docs/commands.md documents every subcommand of `notekit`.

## Verify

Run both before you call a change done:

```bash
python3 -m pytest -q
python3 scripts/lint.py
```
