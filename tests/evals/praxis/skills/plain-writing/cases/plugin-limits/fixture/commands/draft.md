---
description: Draft release notes from merged PRs
---

Draft release notes for the next version from the PRs merged since the last tag.

Limits:

- Never posts anything; it writes `NOTES.md`.
- Leaves out PRs labelled `no-notes`.
- Reads at most 200 PRs.
- Leaves out PRs opened by bots.
- Stops with `gh: rate limited` after 5000 API calls.
