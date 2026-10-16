# Releasing

Grimoire ships several independently versioned plugins from one repository.
Each follows [semantic versioning](https://semver.org) (`MAJOR.MINOR.PATCH`)
and each version gets its own git tag.

## When a version is released

A version is released once it is on `main` in `plugin.json`: a marketplace added
without a ref follows the default branch, and Claude Code updates a plugin when its
`version` changes. Tags serve `#ref` pins, dependency constraints and the GitHub
Release, so tag every version.

## Release a plugin

Releases are git tags named `{plugin-name}--v{version}` (double dash, leading
`v`). Before you start, check that:

- the PR that bumped the version has merged and CI passed on its squash commit on
  `main` (`gh run list --workflow ci.yml --commit <full commit sha>`);
- every plugin it depends on already has a tag its constraint accepts
  ([Dependencies](#dependencies));
- you can push tags to this repository (an agent only when asked: `GUARDRAILS.md`).

Then tag that commit and push the tag:

```bash
git switch --detach <commit>
claude plugin tag plugins/<name> --push
git switch -
```

`claude plugin tag` reads the version from `plugin.json` at that commit, checks the
marketplace entry agrees, and refuses a tag that already exists. `release.yml` then
creates the GitHub Release, with that version's changelog section at the tagged
commit as its body. `gh release view <name>--v<version>` confirms it; a failed run
shows in `gh run list --workflow release.yml`.

## If a release fails

Check `gh release view <name>--v<version>` before any `-f`: `claude plugin tag -f
--push` replaces the tag on GitHub without a warning, even one that has a release,
and `release.yml` still reports success.

**`release.yml` fails with `no entry under a '## <version>' heading`.** No release
exists yet, so the tag may move: land the entry, then at the commit carrying it run

```bash
git switch --detach <commit>
claude plugin tag plugins/<name> -f --push
git switch -
```

The forced push replaces the tag and runs `release.yml` again.

**The tag points at the wrong commit.** `git rev-list -n 1 <name>--v<version>` gives
the tagged commit. The oldest commit that
`git log --reverse -G'"version": "<version>"' -- plugins/<name>/.claude-plugin/plugin.json`
lists set the version. If no release exists, move the tag as above. If one does,
leave the tag and ship any fix as a new version.

**A version shipped something bad.** Users who updated keep that version until the
version changes, so fix forward: fix or revert on a branch with a version bump, and
release that. Never move or delete the bad version's tag: dependency constraints
resolve against it, and a moved tag sends the next install a different commit under
the same version.

## Prereleases

A version carrying a prerelease suffix (`praxis--v2.0.0-rc1`) tags and releases
the same way. `release.yml` marks it a GitHub prerelease, so it stays off the
repo's "Latest" badge.

## Marketplace releases

The per-plugin tags above version a plugin. They do not version the marketplace,
and a consumer's `extraKnownMarketplaces` entry names the repository, not a
plugin. So consumers pin to a second, repo-level tag line:

```text
marketplace-v{MAJOR}.{MINOR}.{PATCH}
```

One dash, not two. `release.yml` triggers on `*--v[0-9]*`, so a double dash would
run it as if `marketplace` were a plugin -- the single dash keeps this line out of
that trigger deliberately.

A tag, not a SHA: a `github` marketplace source takes no `sha`, only a `ref`,
cloned with `git clone --branch`, which rejects a SHA. A tag can be moved, so a
tag ruleset protects `marketplace-v*` from deletion and updates.

After each plugin release, cut the next `marketplace-v*` tag and bump the `ref` in
this repository's `.claude/settings.json`. Merging to `main` alone reaches no
consumer pinned to a `marketplace-v*` tag; consumers pin as
[README.md](README.md) says.

Before tagging, record the release in the root `CHANGELOG.md`: rename
`## Unreleased` to `## <version>`, add each plugin version that changed since the
last marketplace tag, and start a new, empty `## Unreleased` above it.

## Version-bump rules

Claude Code uses a plugin's `version` as the cache key for updates: users only
receive changes when you bump it. Push new commits without a bump and everyone
stays on the cached copy -- `/plugin update` reports "already at the latest
version." Every plugin here declares a `version`, so a change reaches users only
with a bump.

A plugin's version lives in one place: the `"version"` field in
`plugins/<name>/.claude-plugin/plugin.json`. Claude Code resolves the version from
`plugin.json` first and the marketplace entry only as a fallback, so a marketplace
`version` is redundant when it matches and silently overridden by the manifest when
it drifts -- the marketplace entries deliberately carry none.

When you change any content under `plugins/<name>/` (skills, agents, commands,
hooks, README) other than its `CHANGELOG.md`, bump it:

- **PATCH** (`1.0.0` -> `1.0.1`) -- bug fixes, wording, non-behavioural tweaks
- **MINOR** (`1.0.0` -> `1.1.0`) -- new skills/agents/commands, backward-compatible additions
- **MAJOR** (`1.0.0` -> `2.0.0`) -- breaking changes to existing behaviour or invocation

Bump **once per branch, not once per change**. What matters is the delta from
`main`, not how many commits touched the plugin: a branch that fixes some wording
and adds a skill lands a single MINOR bump, not a PATCH followed by a MINOR. A
version already on `main` is released
([When a version is released](#when-a-version-is-released)), so a later branch
bumps again and never folds its changes into that version.

Every bump adds an entry under `## <version>` in `plugins/<name>/CHANGELOG.md`,
saying what changes for someone upgrading; `make verify` fails without one.
Editing only a `CHANGELOG.md` is not a bump trigger.

Editing only a plugin's `marketplace.json` metadata (`description`, `keywords`)
is **not** a bump trigger -- those fields sit outside `plugins/<name>/`, the only
path the bump rule watches.

Version discipline is enforced by **PR review**. Before merging, confirm the bump
rule above holds for every plugin the branch changes. CI gates pure ASCII, JSON
parsing, generated-file drift, per-plugin changelog entries, the test suite and
the full lint set, but nothing there checks the bump rule.

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

`praxis` declares `gitwise`: its `general-reviewer` and `issue-planner` agents
load `gitwise:github-conventions`, and `implement-issue`, `create-pr` and
`address-review` load `gitwise:commit-pr-writing`. Declaring it makes Claude Code
auto-install `gitwise` alongside `praxis`. Add a `dependencies` entry only for a
real requirement like this, and keep its constraint pinned to a tested range.

Because constraints resolve against the `{plugin-name}--v{version}` tags above, a
dependency must be tagged **before or with** the plugin that requires it -- tag
`gitwise` before shipping a `praxis` release that depends on it, or the resolver
has no version to match. See the upstream
[dependency guide](https://code.claude.com/docs/en/plugin-dependencies) for
cross-marketplace rules and conflict resolution.

## Codex

Codex consumes this repo as a marketplace too, so releasing has a second axis:

- **Version bumps do reach Codex users.** The plugin cache is keyed by version
  (`~/.codex/plugins/cache/<marketplace>/<plugin>/<version>`), and an installed
  plugin follows whatever version the marketplace snapshot carries. The bump rule
  above therefore applies unchanged.
- **The `{plugin-name}--v{version}` tags do not.** Codex tracks a git ref for the
  marketplace, not our tags, and refreshes on `codex plugin marketplace upgrade`.
  The tags stay a Claude Code concern, as do `dependencies` -- Codex ignores
  those, which is why `praxis` documents installing `gitwise` explicitly.
- **A bump changes the version in the generated Codex files**: regenerate them
  ([CONTRIBUTING.md](CONTRIBUTING.md)).
