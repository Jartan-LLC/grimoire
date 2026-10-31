# rotakit

## Rules

- Every user-visible change gets a line under `## Unreleased` in CHANGELOG.md.
- docs/examples.md holds a worked example for each subcommand: the command line and what it prints.

## Verify

```bash
python3 -m pytest -q
python3 scripts/lint.py
```
