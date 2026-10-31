# Agent notes

## Rules

- Add a line for each user-visible change under `## Unreleased` in CHANGELOG.md.
- docs/formulas.md names the formula behind each number `brewkit stats` prints.

## Verify

Run both before you call a change done:

```bash
python3 -m pytest -q
python3 scripts/lint.py
```
