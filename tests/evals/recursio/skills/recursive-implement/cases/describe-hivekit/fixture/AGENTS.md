# Agent notes

## Rules

- Add a line for each user-visible change under `## Unreleased` in CHANGELOG.md.
- docs/field-guide.md explains, for club members, each thing `hivekit status` can report about a hive and what to do about it.

## Verify

Run both before you call a change done:

```bash
python3 -m pytest -q
python3 scripts/lint.py
```
