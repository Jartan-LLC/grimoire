---
description: Run review rounds on the current PR while you are away
---

Run review rounds on the current branch's PR until two come back clean, then stop.

Limits:

- Never pushes to `main`, never merges and never force-pushes.
- Stops after 8 rounds.
- Does not run on a PR from a fork.
- Skips the run when `gh` is logged out.
- Ignores draft PRs older than 30 days.
