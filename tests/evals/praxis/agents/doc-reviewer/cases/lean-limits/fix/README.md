# autopilot

A Claude Code plugin that keeps work moving while you are away.

## Install

```text
/plugin install autopilot@acme
```

## Commands

- `/autopilot:walkaway` -- runs review rounds on the current PR until two come back clean. It
  never merges, never pushes to `main` and stops after 8 rounds.
  See `commands/walkaway.md` for all its limits.
