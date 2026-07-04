# Releasing

Grimoire ships several independently versioned plugins from one repository.
Each follows [semantic versioning](https://semver.org) (`MAJOR.MINOR.PATCH`)
and is released with its own git tag.

## Why versions matter

Claude Code uses a plugin's `version` as the cache key for updates: users only
receive changes when you bump it. Push new commits without a bump and everyone
stays on the cached copy — `/plugin update` reports "already at the latest
version." Every plugin here declares a `version`, so **every user-visible change
needs a version bump**.

## Version-bump rules

A plugin's version lives in **two** files that must always agree:

- `plugins/<name>/.claude-plugin/plugin.json` — the `"version"` field
- `.claude-plugin/marketplace.json` — the `"version"` field on that plugin's entry

When you change any content under `plugins/<name>/` (skills, agents, commands,
hooks, README), bump both:

- **PATCH** (`1.0.0` → `1.0.1`) — bug fixes, wording, non-behavioural tweaks
- **MINOR** (`1.0.0` → `1.1.0`) — new skills/agents/commands, backward-compatible additions
- **MAJOR** (`1.0.0` → `2.0.0`) — breaking changes to existing behaviour or invocation

Editing only a plugin's `marketplace.json` metadata (`description`, `keywords`)
is **not** a bump trigger — those fields sit outside `plugins/<name>/`, the only
path the bump rule watches. (The entry's `version` still must match `plugin.json`
— see lockstep below.)

The [pre-push hook](#pre-push-hook) enforces both the bump and the two files
staying in lockstep.

## Tag a release

Releases are resolved from git tags named `{plugin-name}--v{version}` (double
dash, leading `v`), where `{version}` matches that commit's `plugin.json`. Cut
the tag from inside the plugin directory:

```bash
cd plugins/<name>
claude plugin tag --push
```

`claude plugin tag` derives the tag from the manifest, verifies `plugin.json`
and the marketplace entry agree on the version, requires a clean working tree
under the plugin directory, and refuses if the tag already exists; add
`--dry-run` to preview. If the `claude` CLI is unavailable, tag by hand —
equivalent as long as the two files are already in lockstep:

```bash
git tag <name>--v<version>
git push origin <name>--v<version>
```

These tags give each plugin an independent version line and are what dependency
constraints resolve against (see [Dependencies](#dependencies)).

## Pre-push hook

`.githooks/pre-push` blocks a push that changes a plugin's content (relative to
`main`) without a version bump, and rejects any `plugin.json` ↔
`marketplace.json` version mismatch. The bump rule baselines against `main`, so
**one** bump per branch covers all its iterative pushes. The lockstep check runs
across **every** versioned plugin on each push (not only the ones you changed),
so pre-existing version drift anywhere must be fixed before any push succeeds. A
plugin with no `version` field is tolerated (checks skipped with a warning), so
opting out of explicit versioning does not break the hook.

Enable it once per clone:

```bash
git config core.hooksPath .githooks
chmod +x .githooks/pre-push   # git tracks the +x bit; set it if your clone lost it
```

The hook reads JSON with `python3`. Without `python3` it fails **open** — warns
and lets the push through rather than blocking — so treat it as a guard, not a
guarantee; CI or review is the backstop. Bypass in an emergency with `git push
--no-verify`.

## Dependencies

Claude Code plugins may declare inter-plugin dependencies with semver
constraints in `plugin.json`, resolved against the `{plugin-name}--v{version}`
tags above:

```json
{
  "name": "example",
  "version": "1.0.0",
  "dependencies": [
    "other-plugin",
    { "name": "another-plugin", "version": "~1.2.0" }
  ]
}
```

The grimoire plugins have no hard runtime dependencies on one another today, so
none are declared. Add a `dependencies` entry only for a real requirement — it
makes Claude Code auto-install the dependency — and keep its constraint pinned to
a tested range. See the upstream
[dependency guide](https://code.claude.com/docs/en/plugin-dependencies) for
cross-marketplace rules and conflict resolution.

## Release channels

Per-plugin release channels (say, a stable line and a bleeding-edge line) are not
set up. If needed later, express them with a `ref` on the marketplace `source` or
with separate marketplace entries — future work.
