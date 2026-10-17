# Releasing

Grimoire ships several plugins from one repository, each versioned on its own.
Each follows [semantic versioning](https://semver.org) (`MAJOR.MINOR.PATCH`), and
each version gets its own git tag.

## When a version is released

A version is released once it is on `main` in `plugin.json`, because a marketplace
added without a ref follows the default branch and Claude Code updates a plugin when
its `version` changes.

Tag every version anyway: a `#ref` pin to a plugin version, a dependency's version
range ([Dependencies](#dependencies)) and the GitHub Release all point at its tag.

## Tag a version

Merging a version bump to `main` tags and releases it, once CI's verify, lint,
typecheck and test jobs pass on the push. It does not wait for the dev container
build. Then:

1. `ci.yml`'s `release-tags` job (`release-tags.yml`) tags each plugin whose version
   the push changed, tagging a dependency before any plugin that needs it. Each tag is
   `{plugin-name}--v{version}` (double dash, leading `v`), on the push's tip.
2. The job calls `release.yml` for each tag. `release.yml` creates the GitHub
   Release, with that version's changelog section at the tagged commit as its body.

`gh release view <name>--v<version>` confirms the release. The job's log
is in the CI run for that push (`gh run list --workflow ci.yml --commit <full commit sha>`).
A green run can still warn about a version with no tag or a tag on another commit,
so read its warnings too.

A tag the job creates with `GITHUB_TOKEN` starts no workflow, so the job calls
`release.yml` itself. A tag you push by hand still triggers `release.yml` on its own.

## If a release fails

**The `release-tags` job failed.** Re-run its failed jobs
(`gh run rerun --failed <run-id>`). The job creates only the tags that do not exist
yet and never moves one. It passes every tag that exists to `release.yml`, which
skips a GitHub Release that already exists.

If it fails with HTTP 403, the likely cause is a commit changing
`.github/workflows/` that landed on `main` after that push. GitHub refuses a tag
that `GITHUB_TOKEN` creates on a commit whose workflow files differ from `main`'s
tip, so no re-run can create it. Tag the version by hand as below.

**A GitHub Release needs rebuilding** (it was deleted to fix its notes, or it failed
and its CI run can no longer be re-run). Run `release.yml` for the existing tag with
`gh workflow run release.yml -f tag=<name>--v<version>`, or use Run workflow on its
Actions page. It never creates a tag, and it skips a release that already exists.

For a tag from before the per-plugin changelogs (praxis 1.5.0 and earlier, for
one), the run fails without writing anything, since it builds the notes with that
tag's own `scripts/check-changelogs.py --notes`. Recreate that release with
`gh release create <tag> --verify-tag --notes-file <file>`.

**A check failed on the push that bumped a version.** If it was the dev container
build, `release-tags` does not wait on it, so the version is tagged and there is
nothing to do. If it was one of the checks it waits on
([Tag a version](#tag-a-version)), `release-tags` never ran for that push, and no
later push tags the version either, because each run looks only at its own push:

- If the failure was transient, re-run the run's failed jobs. A re-run tests the
  same commit.
- If it was not, or `main`'s workflow files have changed since, tag the version by
  hand at that commit as below.

Do either before the plugin is bumped again: after that, later runs stop warning
that the version has no tag.

**A version needs a tag by hand** (the job cannot run, or the version predates it).
First check that its dependencies have tags their constraints accept
([Dependencies](#dependencies)), and that you may push tags (an agent may only when
asked, per `GUARDRAILS.md`). Then run:

```bash
git switch --detach <commit>
claude plugin tag plugins/<name> --push
git switch -
```

`<commit>` is the commit that set the version: the push's commit in the failed run,
or the oldest commit the `git log` under "The tag points at the wrong commit" lists.

`claude plugin tag` reads the version from `plugin.json` at that commit, checks that
the marketplace entry agrees, and refuses a tag that already exists. The pushed tag
starts `release.yml`, and `gh release view <name>--v<version>` confirms the release.

If `release.yml` then fails with `no entry under a '## <version>' heading`, land
the entry and move the tag to the commit carrying it (`<commit>` below).

Use `-f` only when `gh release view <name>--v<version>` shows no release. It
replaces the tag on GitHub without a warning, even one with a GitHub Release, and
`release.yml` still reports success.

```bash
git switch --detach <commit>
claude plugin tag plugins/<name> -f --push
git switch -
```

The forced push replaces the tag and runs `release.yml` again.

**The tag points at the wrong commit.** `main` takes squash merges only, so each
push is one commit and a tag belongs on the commit that set its version, the oldest
one this lists:

```bash
git log --reverse -G'"version": "<version>"' -- plugins/<name>/.claude-plugin/plugin.json
```

Compare it with the tag, leaving out the changelog so a tag moved to add a missing
entry still passes:

```bash
git diff <that commit> <name>--v<version> -- plugins/<name> ':!plugins/<name>/CHANGELOG.md'
```

If it prints anything, move the tag there with `-f` as above when the version has no
GitHub Release; when it has one, leave the tag and ship any fix as a new version.

When `release-tags` warns that a tag already points at another commit, run the
same `git diff` with the push's commit in place of `<that commit>`. If it prints
anything, the push reused a version number. The check above cannot see that,
because the oldest commit setting the version is the tag's own. Leave the tag and
ship the push's content as a new version.

**A version shipped something bad.** Users who updated keep that version until the
version changes, so fix forward: fix or revert on a branch with a version bump, and
release that. Never move or delete the bad version's tag. Dependency constraints
resolve against it, and a moved tag sends the next install a different commit under
the same version.

## Prereleases

A version with a prerelease suffix (`praxis--v2.0.0-rc1`) tags and releases the
same way. `release.yml` marks it a GitHub prerelease, so it stays off the repo's
"Latest" badge.

## Marketplace releases

The per-plugin tags above version a plugin, not the marketplace. A consumer's
`extraKnownMarketplaces` entry names the repository, not a plugin, so consumers pin
to a second, repo-level tag line:

```text
marketplace-v{MAJOR}.{MINOR}.{PATCH}
```

One dash keeps these tags out of `release.yml`'s `*--v[0-9]*` trigger. Consumers
pin a tag because a `github` marketplace source takes only a `ref`, cloned with
`git clone --branch`, which rejects a SHA. A tag can be moved, so a tag ruleset
protects `marketplace-v*` from deletion and updates.

Cut the next `marketplace-v*` tag when the maintainer decides pinned consumers
should pick up the plugin releases since the last one. A plugin release alone does
not call for one. Until then, merging to `main` reaches no consumer pinned to a
`marketplace-v*` tag. Consumers pin as [README.md](README.md) says.

To cut one:

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

Claude Code uses a plugin's `version` as the cache key for updates. Push new commits
without a bump and everyone stays on the cached copy: `/plugin update` reports
"already at the latest version." Every plugin here declares a `version`, so a
change reaches users only with a bump.

A plugin's version lives only in `plugins/<name>/.claude-plugin/plugin.json`. Claude
Code reads it there before the marketplace entry, so the marketplace entries carry
no `version`: a matching one would be redundant, and a drifting one silently
overridden.

When you change any content under `plugins/<name>/` (skills, agents, commands,
hooks, README) other than its `CHANGELOG.md`, bump it:

- **PATCH** (`1.0.0` -> `1.0.1`): bug fixes, wording, non-behavioural tweaks
- **MINOR** (`1.0.0` -> `1.1.0`): new skills/agents/commands, backward-compatible additions
- **MAJOR** (`1.0.0` -> `2.0.0`): breaking changes to existing behaviour or invocation

Bump once per branch, not once per change. The bump covers the branch's delta from
`main`, however many commits touched the plugin. A branch that fixes some wording
and adds a skill lands a single MINOR bump, not a PATCH followed by a MINOR.

A version already on `main` is released
([When a version is released](#when-a-version-is-released)), so a later branch bumps
again and never folds its changes into that version.

Every bump adds an entry under `## <version>` in `plugins/<name>/CHANGELOG.md`,
saying what changes for someone upgrading. `make verify` fails without one.

Editing only a plugin's `CHANGELOG.md`, or only its `marketplace.json` metadata
(`description`, `keywords`, which sit outside `plugins/<name>/`), needs no bump.

No CI check enforces the bump rule, so PR review does: before merging, confirm it
holds for every plugin the branch changes.

## Dependencies

A plugin can declare dependencies on other plugins in `plugin.json`, with semver
constraints that resolve against the `{plugin-name}--v{version}` tags above:

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

`praxis` declares `gitwise`. Its `general-reviewer` and `issue-planner` agents
load `gitwise:github-conventions`, and `implement-issue`, `create-pr` and
`address-review` load `gitwise:commit-pr-writing`. Declaring the dependency makes
Claude Code auto-install `gitwise` alongside `praxis`.

Add a `dependencies` entry only for a real requirement like this, and keep its
constraint pinned to a tested range.

`make verify` fails a malformed entry, a dependency on a plugin this marketplace
does not have (an entry naming another marketplace is checked only for its shape),
and a range the in-repo version of that plugin does not meet. It
reads ranges as node-semver does (Claude Code uses node-semver), but only the `^`,
`~` and exact forms, and fails a range it cannot check. `accepts()` in
`scripts/check-changelogs.py` lists the cases.

Tag a dependency before or with the plugin that requires it. `release-tags` does
this within a push.

These plugins have relative-path sources: each marketplace entry points to the
plugin's folder in this repository. So when no tag meets a range, Claude Code uses
the marketplace's current copy of the dependency and checks the range when the
plugin loads. The range check that `make verify` runs keeps that copy inside the
range.

See the upstream
[dependency guide](https://code.claude.com/docs/en/plugin-dependencies) for
cross-marketplace rules and conflict resolution.

## Codex

Codex also uses this repo as a marketplace, so releasing has to account for it too:

- Version bumps do reach Codex users. The plugin cache is keyed by version
  (`~/.codex/plugins/cache/<marketplace>/<plugin>/<version>`), and an installed
  plugin follows whatever version the marketplace snapshot carries. The bump rule
  above applies unchanged.
- Codex does not use the `{plugin-name}--v{version}` tags. It tracks a git ref for
  the marketplace and refreshes on `codex plugin marketplace upgrade`. It also
  ignores `dependencies`, which is why `praxis` documents installing `gitwise`
  explicitly.
- A bump changes the version in the generated Codex files, so regenerate them
  ([CONTRIBUTING.md](CONTRIBUTING.md)).
