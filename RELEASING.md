# Releasing

## When a version is released

A version is released once `plugin.json` on `main` carries it: a marketplace added
without a ref follows the default branch.

Each version still needs its tag: dependency ranges resolve against it, and its
GitHub Release is built from it.

## Tag a version

Merging a version bump to `main` tags it and creates its GitHub Release, once CI's
verify, lint, typecheck and test jobs pass on the push. It does not wait for the
dev container build.

`release-tags` (`release-tags.yml`) tags each plugin version the push changed as
`{plugin-name}--v{version}` (double dash, leading `v`) at the push's commit, a
dependency before the plugin that needs it. It then calls `release.yml`, which
creates the GitHub Release from that version's changelog section at the tagged
commit.

`gh release view <name>--v<version>` confirms the release. The job's log
is in the CI run for that push (`gh run list --workflow ci.yml --commit <full commit sha>`).
A green run can still warn about a version with no tag or a tag on another commit,
so read its warnings too.

## If a release fails

**The `release-tags` job failed.** Re-run its failed jobs
(`gh run rerun --failed <run-id>`). The job creates only the tags that do not exist
yet and never moves one. It passes every tag that exists to `release.yml`, which
skips a GitHub Release that already exists.

If it failed with HTTP 403, likely because `main`'s workflow files changed after
that push, no re-run can create the tag: tag the version by hand as below.

**A GitHub Release needs rebuilding** (it was deleted to fix its notes, or it failed
and its CI run can no longer be re-run). Run `release.yml` for the existing tag with
`gh workflow run release.yml -f tag=<name>--v<version>`, or use Run workflow on its
Actions page. It never creates a tag, and it skips a release that already exists.

For a tag from before per-plugin changelogs (praxis 1.5.0 and earlier, for one),
that run fails; recreate the release with
`gh release create <tag> --verify-tag --notes-file <file>`.

**A check failed on the push that bumped a version.** If it was not one of the
checks `release-tags` waits on ([Tag a version](#tag-a-version)), such as the dev
container build, the version is tagged and there is nothing to do. If it was one of
them, `release-tags` never ran for that push, and no later push tags the version
either, because each run looks only at its own push:

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

The pushed tag starts `release.yml`; confirm it as above.

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
anything, the push reused a version number: leave the tag and ship the push's
content as a new version.

**A version shipped something bad.** Fix forward: fix or revert on a branch with a
version bump, and release that. Never move or delete the bad version's tag:
dependency ranges resolve against it, and a moved tag serves the next install
different content under the same version.

## Prereleases

A prerelease version (`2.0.0-rc1`) tags and releases the same way, as a GitHub
prerelease.

## Marketplace releases

Consumers pin the whole marketplace to a `marketplace-v{MAJOR}.{MINOR}.{PATCH}` tag
([README.md](README.md) shows how), a tag line separate from the per-plugin tags.

One dash keeps these tags out of `release.yml`'s `*--v[0-9]*` trigger. A tag
ruleset blocks moving or deleting a `marketplace-v*` tag, so check the commit
before you push one.

Cut the next `marketplace-v*` tag when the maintainer wants pinned consumers to get
the plugin releases since the last one; a plugin release alone does not call for
one.

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

A change reaches users only when the plugin's `version` changes
([upstream](https://code.claude.com/docs/en/plugins/host-marketplace#release-a-new-version)).

A plugin's version lives only in `plugins/<name>/.claude-plugin/plugin.json`.
Marketplace entries carry no `version`: Claude Code would silently prefer
`plugin.json`'s.

When you change any content under `plugins/<name>/` (skills, agents, commands,
hooks, README) other than its `CHANGELOG.md`, bump it:

- **PATCH** (`1.0.0` -> `1.0.1`): bug fixes, wording, non-behavioural tweaks
- **MINOR** (`1.0.0` -> `1.1.0`): new skills/agents/commands, backward-compatible additions
- **MAJOR** (`1.0.0` -> `2.0.0`): breaking changes to existing behaviour or invocation

Bump once per branch, at the level of the branch's whole delta from `main`: a
branch that fixes wording and adds a skill lands one MINOR bump.

A version already on `main` is released
([When a version is released](#when-a-version-is-released)), so a later branch bumps
again and never folds its changes into that version.

Every bump adds an entry under `## <version>` in `plugins/<name>/CHANGELOG.md`,
saying what changes for someone upgrading. `make verify` fails without one.

Editing only a plugin's `CHANGELOG.md`, or only its `description` in
`marketplace.json`, needs no bump. Its marketplace `keywords` and `category` are
different: `scripts/generate-codex.py` copies them into
`plugins/<name>/.codex-plugin/plugin.json`, so the bump rule applies.

No CI check enforces the bump rule, so PR review does: before merging, confirm it
holds for every plugin the branch changes.

## Dependencies

A plugin declares dependencies in `plugin.json` (syntax and resolution: the
upstream [dependency guide](https://code.claude.com/docs/en/plugins/dependencies));
version ranges resolve against the `{plugin-name}--v{version}` tags above.

Add a `dependencies` entry only for a real runtime requirement, such as `praxis`'s
agents loading `gitwise` skills, and keep its constraint pinned to a tested range.
`make verify` fails a skill, agent or command that loads or names another plugin its
manifest does not declare (`scripts/check-wiring.py`).

Codex ignores `dependencies`, so a plugin that declares one says in its README how
to install it in Codex, as praxis does.

Write ranges as `^`, `~` or exact versions: `make verify` checks each against the
in-repo version of the dependency (an entry naming another marketplace only for its
shape) and fails any range it cannot check (`accepts()` in `scripts/check-changelogs.py`).
