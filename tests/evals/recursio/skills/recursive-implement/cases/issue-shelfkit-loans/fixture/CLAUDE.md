# shelfkit

## Rules

- Every user-visible change gets a line under `## Unreleased` in CHANGELOG.md.
- The README's Command section shows every subcommand with an example.

## Verify

```bash
python3 -m pytest -q
python3 scripts/lint.py
```
