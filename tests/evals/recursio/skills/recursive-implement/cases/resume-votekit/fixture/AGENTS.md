# Agent notes

## Rules

- Add a line for each user-visible change under `## Unreleased` in CHANGELOG.md.
- docs/example.md walks through a sample election: a ballot file, the `votekit count` command run on it, and its output.

## Verify

Run both before you call a change done:

```bash
python3 -m pytest -q
python3 scripts/lint.py
```
