# Agent notes

## Rules

- Add a line for each user-visible change under `## Unreleased` in CHANGELOG.md.
- docs/marking.md tells teachers how a quiz is marked, with `quizkit grade` and `quizkit items` run on a small example.

## Verify

Run both before you call a change done:

```bash
python3 -m pytest -q
python3 scripts/lint.py
```
