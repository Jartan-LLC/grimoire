# dotlink

A Dev Container Feature that links your dotfiles into every container.

## Install

```json
"features": {
  "ghcr.io/acme/features/dotlink:1": {}
}
```

## What it changes

Mount your dotfiles repository at `/opt/dotfiles` first. When the container starts, dotlink links each
file in it into your home directory. A file it replaces is kept as `<file>.orig`; move it back to undo
the link.
