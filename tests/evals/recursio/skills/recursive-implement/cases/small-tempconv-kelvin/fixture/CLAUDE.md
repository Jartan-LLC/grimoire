# tempconv

## Rules

- Every user-visible change gets a line under `## Unreleased` in CHANGELOG.md.
- The README's Usage section documents every option and every unit.

## Verify

```bash
prove -l t
perl scripts/lint.pl
```
