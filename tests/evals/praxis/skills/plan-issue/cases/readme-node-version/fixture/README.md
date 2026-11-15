# icsmerge

Merge the calendars your team exports into one file you can subscribe to:

```bash
npx icsmerge holidays.ics oncall.ics releases.ics > team.ics
```

An event that appears in more than one file (same `UID`) is kept once.

## Requirements

Node 16 or later.
