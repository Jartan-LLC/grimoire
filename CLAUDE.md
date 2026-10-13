# Grimoire

A Claude Code plugin marketplace. Each plugin lives in `plugins/<name>/` with a
`.claude-plugin/plugin.json` manifest and a mirrored entry in
`.claude-plugin/marketplace.json`.

## Rules

The project rules live in `GUARDRAILS.md`, ranked by how firmly each holds; this import
loads them into every session:

@GUARDRAILS.md

## Corrections

## Skills

## Verify

Run `make check` before declaring work done -- it runs CI's lint, typecheck and verify checks:

```bash
make check
```

`make help` lists the individual targets. `AGENTS.md` is a symlink to this file, not a
second source of truth -- edit `CLAUDE.md`.

Then confirm by inspection: each skill/agent frontmatter `name` matches its directory, and
any plugin with changes under `plugins/<name>/` other than its `CHANGELOG.md` has a bumped
`version` in `plugin.json`.
