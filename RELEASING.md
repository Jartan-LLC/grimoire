# Releasing

Grimoire ships several independently versioned plugins from one repository.
Each follows [semantic versioning](https://semver.org) (`MAJOR.MINOR.PATCH`)
and each version gets its own git tag.

## When a version is released

A version is released once it is on `main` in `plugin.json`: a marketplace added
without a ref follows the default branch, and Claude Code updates a plugin when its
`version` changes. Tags serve `#ref` pins, dependency constraints and the GitHub
Release, so tag every version.

## Tag a version

Merging a version bump to `main` tags and releases it. Once CI's verify, lint,
typecheck and test jobs pass on the push (the dev container build is not waited
for), `ci.yml`'s `release-tags` job (`release-tags.yml`) creates a
`{plugin-name}--v{version}` tag (double dash, leading `v`) at the push's tip for each
plugin whose version the push changed, a dependency before the plugin that needs
it, and calls `release.yml` for each. `release.yml` creates the GitHub Release, with
that version's changelog section at the tagged commit as its body. To confirm,
`gh release view <name>--v<version>` shows the release, and the job's log is in the
CI run for that push (`gh run list --workflow ci.yml --commit <full commit sha>`).
A green run can still warn, about a version with no tag or a tag on another commit,
so read its warnings too.

The job creates tags through the API with `GITHUB_TOKEN`, and a tag created that way
starts no workflow, so `release.yml` runs because the job calls it, not on the tag
push. A tag you push by hand still triggers `release.yml` on its own.

## If a release fails

**The `release-tags` job failed.** Re-run its failed jobs
(`gh run rerun --failed <run-id>`): the job creates only the tags that do not exist
yet, never moves one, and passes every tag that exists to `release.yml`, which skips
a GitHub Release that already exists. If it fails with HTTP 403, the likely cause is
a commit changing `.github/workflows/` that landed on `main` after that push: GitHub
refuses a tag that `GITHUB_TOKEN` creates on a commit whose workflow files differ
from `main`'s tip, so no re-run can create it. Tag the version by hand as below.

**A GitHub Release needs rebuilding** (it was deleted to fix its notes, or it failed
and its CI run can no longer be re-run). Run `release.yml` for the existing tag:
`gh workflow run release.yml -f tag=<name>--v<version>`, or Run workflow on its
Actions page. It never creates a tag, and it skips a release that already exists.
It builds the notes with `scripts/check-changelogs.py --notes` at the tag, which tags
from before the per-plugin changelogs (praxis 1.5.0 and earlier, for one) lack; there
the run fails without writing anything, so recreate the release by hand with
`gh release create <tag> --verify-tag --notes-file <file>`.

**One of the checks `release-tags` waits on failed on the push that bumped a
version.** `release-tags` never ran for that push, and no later push tags the
version: each run looks only at its own push. If the failure was transient, re-run
the run's failed jobs (a re-run tests the same commit). If it was not, or `main`'s
workflow files have changed since, tag the version by hand at that commit as below.
Do either before the plugin is bumped again: each later run's log warns that the
version has no tag only while it is still that plugin's current version.

**A version needs a tag by hand** (the job cannot run, or the version predates it).
Check that its dependencies have tags their constraints accept
([Dependencies](#dependencies)) and that you may push tags (an agent only when
asked: `GUARDRAILS.md`), then:

```bash
git switch --detach <commit>
claude plugin tag plugins/<name> --push
git switch -
```

`<commit>` is the commit that set the version: the push's commit in the failed run,
or the oldest commit the `git log` under "The tag points at the wrong commit" below
lists. `claude plugin tag`
reads the version from `plugin.json` at that commit, checks the marketplace entry
agrees, and refuses a tag that already exists. The pushed tag starts `release.yml`;
`gh release view <name>--v<version>` confirms the release.

Check `gh release view <name>--v<version>` before any `-f`: `claude plugin tag -f
--push` replaces the tag on GitHub without a warning, even one that has a GitHub
Release, and `release.yml` still reports success.

**`release.yml` fails with `no entry under a '## <version>' heading`.** This needs a
hand-pushed tag, since CI fails a version on `main` without its entry. No GitHub
Release exists yet, so the tag may move: land the entry, then at the commit carrying
it run

```bash
git switch --detach <commit>
claude plugin tag plugins/<name> -f --push
git switch -
```

The forced push replaces the tag and runs `release.yml` again.

**The tag points at the wrong commit.** `main` takes squash merges only, so a push
carries one commit and the tag sits on the commit that set the version. The oldest
commit that
`git log --reverse -G'"version": "<version>"' -- plugins/<name>/.claude-plugin/plugin.json`
lists set the version. The tag is wrong when the plugin's files differ there:
`git diff <that commit> <name>--v<version> -- plugins/<name> ':!plugins/<name>/CHANGELOG.md'`
prints anything (a tag moved to the commit carrying a missing changelog entry
prints nothing). If no GitHub Release exists, move the tag as above. If one does,
leave the tag and ship any fix as a new version.

When `release-tags` warns that a due tag already points at another commit, compare
the two commits the warning names instead:
`git diff <tag's commit> <push's commit> -- plugins/<name> ':!plugins/<name>/CHANGELOG.md'`.
If it prints anything, the push reused a version number, and the check above cannot
see it (the oldest commit setting that version is the tag's own). Leave the tag and
ship the push's content as a new version.

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

Cut the next `marketplace-v*` tag when the maintainer decides pinned consumers
should pick up the plugin releases since the last one; a plugin release alone does
not call for one. Until then, merging to `main` reaches no consumer pinned to a
`marketplace-v*` tag, and consumers pin as [README.md](README.md) says. To cut one:

1. In a PR, record the release in the root `CHANGELOG.md`: rename
   `## Unreleased` to `## <version>`, add each plugin version that changed since
   the last marketplace tag, and start a new, empty `## Unreleased` above it.
2. Once it merges, tag its squash commit and push the tag:

   ```bash
   git tag marketplace-v<version> <commit>
   git push origin marketplace-v<version>
   ```

3. In a PR, bump the `ref` in this repository's `.claude/settings.json` to the new
   tag.

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
parsing, generated-file drift, per-plugin changelog entries, plugin directories named
like their manifests, in-tree dependency names and ranges, the test suite and the full
lint set, but nothing there checks the bump rule.

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
`make verify` fails a malformed dependency entry, a dependency on a plugin this
marketplace does not have (an entry naming no marketplace, or this one, must name a
plugin here), and a range on a plugin in this repository that the depended-on
plugin's version here does not meet. It reads `^X.Y.Z`, `~X.Y.Z` and an exact
`X.Y.Z` or `=X.Y.Z` and rejects a prerelease version as node-semver (which Claude
Code resolves ranges with) does. It also fails, as a range it cannot check, any
other range form, a prerelease version under a range that opts into that version's
prereleases, and a version with build metadata.

Constraints resolve against the `{plugin-name}--v{version}` tags above, so tag a
dependency **before or with** the plugin that requires it (`release-tags` does so
within a push). These plugins have relative-path sources, so when no tag meets a
range, Claude Code uses the marketplace's current copy of the dependency and checks
the range when the plugin loads; the range check `make verify` runs keeps that copy
inside the range. See the upstream
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
