# nightly

A Claude Code plugin for unattended repository chores.

## Install

```text
/plugin install nightly@acme
```

## Commands

- `/nightly:triage` -- labels each new issue by its content. It never closes or comments on an
  issue and labels at most 20 issues a run.
  See `commands/triage.md` for all its limits.
