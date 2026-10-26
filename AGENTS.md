# Grimoire

A Claude Code plugin marketplace. Each plugin lives in `plugins/<name>/` with a
`.claude-plugin/plugin.json` manifest and a mirrored entry in
`.claude-plugin/marketplace.json`.

## Rules

The project rules live in `GUARDRAILS.md`, ranked by how firmly each holds. Claude Code
loads them through the import below; any other agent reads `GUARDRAILS.md` before
starting work.

@GUARDRAILS.md

## Corrections

## Skills

## Verify

Run `make check` before declaring work done -- it runs CI's lint, typecheck, test and verify checks:

```bash
make check
```

`make help` lists the individual targets. `CLAUDE.md` only imports this file, for Claude
Code -- edit `AGENTS.md`.

Then confirm by inspection: any plugin with changes under `plugins/<name>/` other than its
`CHANGELOG.md` has a bumped `version` in `plugin.json`.
