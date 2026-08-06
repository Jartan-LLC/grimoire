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

Bump **once per release, not once per change**. The version is a cache key
against the last released version, so what matters is the delta from `main`, not
how many commits touched the plugin. A branch that fixes some wording and adds a
skill lands a single MINOR bump, not a PATCH followed by a MINOR.

Editing only a plugin's `marketplace.json` metadata (`description`, `keywords`)
is **not** a bump trigger -- those fields sit outside `plugins/<name>/`, the only
path the bump rule watches.

## Enforcement

Version discipline is enforced by **PR review**. Before merging, confirm any
plugin with changed content under `plugins/<name>/` has a bumped `version` in its
`plugin.json`. CI gates pure ASCII, JSON parsing, generated-file drift and the
full lint set, but nothing there checks the bump rule.

## Tag a release

Releases are resolved from git tags named `{plugin-name}--v{version}` (double
dash, leading `v`), where `{version}` matches that commit's `plugin.json`. Tag
the merge commit and push:

```bash
git tag <name>--v<version>
git push origin <name>--v<version>
```

The version in the tag must match `plugin.json` at that commit, and the tag must
not already exist -- nothing checks either for you, and a tag pointing at the
wrong commit is what the resolver will hand users.

These tags give each plugin an independent version line and are what dependency
constraints resolve against (see [Dependencies](#dependencies)).

Pushing the tag is the only manual step: `release.yml` creates the GitHub
Release from it. The body is a fixed pointer, not generated notes -- GitHub's
generated notes diff repo-wide and would attribute other plugins' commits to
this release. The changelog lives in the commit history and the per-plugin tags.

A version carrying a prerelease suffix (`praxis--v2.0.0-rc1`) tags and releases
the same way. `release.yml` marks it a GitHub prerelease, so it stays off the
repo's "Latest" badge.

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
  agents, and commit the result.
- **`--check` fails on more than staleness**: a generated file out of date with
  its source, an orphan whose source is gone, and a duplicated hook script whose
  copies have diverged.

## Duplicated hook scripts

Some hook scripts ship from more than one plugin and must stay byte-identical;
`generate-codex.py` names them in `DUPLICATED_HOOK_SCRIPTS`. Edit every copy in
the same commit, or `--check` fails. Each plugin shipping one has changed content
under `plugins/<name>/`, so each takes its own version bump.

Expect `find-duplicate-comments.js` to report every comment in these copies as
retold, and dismiss it.

## Release channels

Per-plugin release channels (say, a stable line and a bleeding-edge line) are not
set up. If needed later, express them with a `ref` on the marketplace `source` or
with separate marketplace entries -- future work.
