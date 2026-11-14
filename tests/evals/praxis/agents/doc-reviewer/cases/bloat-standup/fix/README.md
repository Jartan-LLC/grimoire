# standup

A Claude Code plugin that writes the daily standup.

## Install

```text
/plugin install standup@acme
```

## Commands

- `/standup:post` -- posts the commits and merged PRs of the last working day to the team channel.
  It posts at most once a day and never to a channel it has not been added to. It skips weekends
  and the holidays in the team calendar, and leaves out commits made by bots.
