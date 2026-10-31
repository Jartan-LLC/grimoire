# isbntool

## Rules

- Every user-visible change gets a line under `## Unreleased` in CHANGELOG.md.
- The README's Usage section documents every subcommand and option.

## Verify

```bash
python3 -m pytest -q
python3 scripts/lint.py
```
