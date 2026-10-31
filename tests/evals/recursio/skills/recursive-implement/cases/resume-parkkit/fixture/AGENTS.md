# Agent notes

## Rules

- Add a line for each user-visible change under `## Unreleased` in CHANGELOG.md.
- docs/pricing.md walks through a sample bill: a rates file, a ticket, and how `parkkit fees` works out its fee.

## Verify

Run both before you call a change done:

```bash
node --test
node scripts/lint.js
```
