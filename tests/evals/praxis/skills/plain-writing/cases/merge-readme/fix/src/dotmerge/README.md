# dotmerge

A Dev Container Feature that gives every container the team's tool settings.

## Install

```json
"features": {
  "ghcr.io/acme/features/dotmerge:1": {}
}
```

## What it changes

When the container starts, dotmerge merges the team's settings into
`~/.config/tool/settings.json`. Your own values win where both set a key. Your original file is
kept as `settings.json.pre-dotmerge`; copy it back to undo the merge.
