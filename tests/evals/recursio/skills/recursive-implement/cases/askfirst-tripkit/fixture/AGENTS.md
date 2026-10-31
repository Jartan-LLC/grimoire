# Agent notes

## Rules

- tripkit must work with no connection: it runs on planes and in the mountains. Ask the maintainer before adding any network access, in code or in tests.
- Add a line for each user-visible change under `## Unreleased` in CHANGELOG.md.
- docs/howto.md shows travellers how to split a trip's costs, with `tripkit balances` and `tripkit settle` run on an example.

## Verify

Run both before you call a change done:

```bash
node --test
node scripts/lint.ts
```
