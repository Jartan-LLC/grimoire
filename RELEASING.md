# Releasing

Grimoire ships several independently versioned plugins from one repository.
Each follows [semantic versioning](https://semver.org) (`MAJOR.MINOR.PATCH`)
and is released with its own git tag.

## Why versions matter

Claude Code uses a plugin's `version` as the cache key for updates: users only
receive changes when you bump it. Push new commits without a bump and everyone
stays on the cached copy -- `/plugin update` reports "already at the latest
version." Every plugin here declares a `version`, so **every user-visible change
needs a version bump**.

## Version-bump rules

A plugin's version lives in one place: the `"version"` field in
`plugins/<name>/.claude-plugin/plugin.json`. Claude Code resolves the version from
`plugin.json` first and the marketplace entry only as a fallback, so a marketplace
`version` is redundant when it matches and silently overridden by the manifest when
it drifts -- the marketplace entries deliberately carry none.

When you change any content under `plugins/<name>/` (skills, agents, commands,
hooks, README), bump it:

- **PATCH** (`1.0.0` -> `1.0.1`) -- bug fixes, wording, non-behavioural tweaks
- **MINOR** (`1.0.0` -> `1.1.0`) -- new skills/agents/commands, backward-compatible additions
- **MAJOR** (`1.0.0` -> `2.0.0`) -- breaking changes to existing behaviour or invocation

Editing only a plugin's `marketplace.json` metadata (`description`, `keywords`)
is **not** a bump trigger -- those fields sit outside `plugins/<name>/`, the only
path the bump rule watches.

The bump is enforced by review (see [Enforcement](#enforcement)).

## Tag a release

Releases are resolved from git tags named `{plugin-name}--v{version}` (double
dash, leading `v`), where `{version}` matches that commit's `plugin.json`. Cut
the tag from inside the plugin directory:

```bash
cd plugins/<name>
claude plugin tag --push
```

`claude plugin tag` derives the tag from `plugin.json`, requires a clean working
tree under the plugin directory, and refuses if the tag already exists; add
`--dry-run` to preview. (Its check that `plugin.json` and the marketplace entry
agree on the version is moot here -- the marketplace entries carry none.) If the `claude` CLI is unavailable, tag by hand:

```bash
git tag <name>--v<version>
git push origin <name>--v<version>
```

These tags give each plugin an independent version line and are what dependency
constraints resolve against (see [Dependencies](#dependencies)).

Pushing a `{plugin}--v{version}` tag auto-creates the GitHub Release, so
`claude plugin tag --push` is the only manual step. The body is a fixed pointer,
not generated notes -- GitHub's generated notes diff repo-wide and would
attribute other plugins' commits to this release. The changelog lives in the
commit history and the per-plugin tags.

## Enforcement

Version discipline is enforced by **PR review**. Before merging, confirm any
plugin with changed content under `plugins/<name>/` has a bumped `version` in its
`plugin.json`. CI runs the `CLAUDE.md` Verify block on every pull request, but
that covers ASCII, JSON and generated-file drift -- not the bump rule, which
still needs a human. (A CI check could automate it later.)

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

`praxis` declares `gitwise` (`^1.0.0`): its reviewer and planner agents load the
`gitwise:github-conventions` skill, so `gitwise` must be present for them to
resolve. Declaring it makes Claude Code auto-install `gitwise` alongside
`praxis`. Add a `dependencies` entry only for a real requirement like this, and
keep its constraint pinned to a tested range.

Because constraints resolve against the `{plugin-name}--v{version}` tags above, a
dependency must be tagged **before or with** the plugin that requires it -- tag
`gitwise` before shipping a `praxis` release that depends on it, or the resolver
has no version to match. See the upstream
[dependency guide](https://code.claude.com/docs/en/plugin-dependencies) for
cross-marketplace rules and conflict resolution.

## Codex

Codex consumes this repo as a marketplace too, so releasing has a second axis.
Verified against codex-cli 0.146.0:

- **Version bumps do reach Codex users.** The plugin cache is keyed by version
  (`~/.codex/plugins/cache/<marketplace>/<plugin>/<version>`), and an installed
  plugin follows whatever version the marketplace snapshot carries. The bump rule
  above therefore applies unchanged.
- **The `{plugin-name}--v{version}` tags do not.** Codex tracks a git ref for the
  marketplace, not our tags, and refreshes on `codex plugin marketplace upgrade`.
  The tags stay a Claude Code concern, as do `dependencies` -- Codex ignores
  those, which is why `praxis` documents installing `gitwise` explicitly.
- **The Codex files are generated -- never hand-edit them.** That means
  `plugins/<name>/.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`,
  and `plugins/<name>/codex/agents/*.toml`. Run `scripts/generate-codex.py` after
  any change to a plugin's name, version, description, keywords, category, or
  agents, and commit the result. `--check` fails when they are stale or orphaned.

## Release channels

Per-plugin release channels (say, a stable line and a bleeding-edge line) are not
set up. If needed later, express them with a `ref` on the marketplace `source` or
with separate marketplace entries -- future work.
