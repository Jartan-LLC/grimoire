# Reviewing releasing changes

Checks for a change to a release procedure (a RELEASING.md, a checklist, a release section). Where
the project's own rules, checks or tools decide a point, raise nothing against them. Review first against
`releasing.md` in the docs-patterns skill, then these checks. Apply them to text the change adds or
alters and to steps its workflow edits make wrong; raise other problems in the file as suggestions.

## Steps and commands

**Run order, commands and the target commit.** Each manual step appears in run order, with its exact command
or web page (an edit or review step needs neither), a placeholder wherever a version goes, and the commit or
branch a tag or publish targets. A step some releases skip names a condition checkable in the repository or
on the forge, or the decider the project names. A condition or decider the author supplies for
a choice nobody made is policy (see below).

- Prevents: a copied command that tags the wrong version, or a tag on a commit the main branch never gets.
- Severity: a step that publishes or tags the wrong version or commit to a channel that cannot take it
  back (a crates.io or PyPI version, an image users pulled) is Critical, else Important.
- Verify: read the steps against the release workflow's trigger and the merge settings; look for literal
  versions in commands. A literal version in example output is at most a Minor suggestion.
- Bad: `cargo set-version --workspace 4.0.0-rc.1`; "6. Optional: create a GitHub release from the tag", where
  the project names no condition. Better: `X.Y.Z-rc.N`; a condition the project states ("A tag with a
  pre-release part ... is published as a pre-release"), or the step left out and raised in the PR description.

**Claims about checks, protections and commands.** Every statement that something checks, protects or
publishes, that nothing does, or that a command works must match what the repository shows. A command copied
from a workflow comment, or behaviour assumed from how a tool usually works, does not count as checked.

- Prevents: a releaser skipping a check the document says a ruleset or workflow makes.
- Verify: read-only `gh api repos/OWNER/REPO/rulesets` and `.../environments`; `git tag -l` and
  `gh release list`; the workflow file for what a push or re-run does; a command's `--help` or dry run; the
  registry's version list. A setting your token cannot read is a question for an admin.
- Bad: "a tag ruleset protects `marketplace-v*`" while the ruleset matched `refs/tags/refs/tags/marketplace-*`;
  "The Check Semver workflow runs cargo-semver-checks on the release PR like any other PR" where the release
  PR is opened with `GITHUB_TOKEN` (GitHub starts no `pull_request` workflows for it);
  `gh release verify OWNER/REPO vX.Y.Z`, never run.
- Better: `gh release verify vX.Y.Z -R OWNER/REPO`, once run; a claim nobody could confirm goes to the PR
  description.
- A step no past release ran (per the tags and `gh release list`): raise it as a question, and as a finding
  if the change presents it as the established procedure.
- Raise nothing on a precondition list that does not say which items a machine enforces; a stated check,
  or its absence, is verified as above.

## After the last manual step

**What runs on its own, and how to confirm it.** The text says what runs without the releaser, where it
publishes, what waits on them (an approval, an environment) and when they are done. Where a step can
be skipped or fail silently, it says how to confirm each place got the release.

- Prevents: a channel silently missing a version, such as a hand-made release page one release forgot.
- Verify: read every workflow triggered by the tag, the release or the merge; compare `git tag -l` with
  `gh release list`. A failed run that notifies the releaser counts as reported; a ticked checklist line
  counts as the confirm.

**Tracing a version to its commit.** Where no tag records which commit a published version came from, the
text says how to find it. Raise nothing where each version has a tag.

- Prevents: a recovery that cannot find the commit a bad version came from.
- Verify: run `git log --reverse -G'<line>' -- <manifest>` on the manifest's version line
  (`"version": "X.Y.Z"` in package.json, `version = "X.Y.Z"` in Cargo.toml): the oldest commit listed set it.
  A tag whose `git rev-list -n 1 <tag>` differs from that commit is on the wrong commit. For an image, its
  `org.opencontainers.image.revision` label (`skopeo inspect`).

## Recovery

**A wrong recovery step is Critical.** A recovery command is also a claim; file one finding, at this
severity. Each recovery or retry step states the condition it is safe under. If neither the workflow file nor
the PR description shows it was run or dry-run, report it as Critical with status suspected, as a question.

- Prevents: a retry that publishes the wrong commit or moves a version users pulled.
- Verify: a re-run of a failed workflow builds the tagged commit again, so "fix the cause and re-run it"
  fits only a transient failure. A forced tag push (`git push -f`, a tag tool's `--force`) can move a tag that
  already has a release; nothing on the forge reports the move, and a release workflow that skips an existing
  release still passes. Before any step that moves or re-creates a tag, check `gh release view <tag>` (and the
  registry); the step must say what to do when a release already exists.
- Bad: "To retry, re-run the failed job from the Actions tab", for a deploy job that force-pushes HEAD (an
  older run rolls the app back). Better: no retry step; the PR description asks the maintainers how a failed
  deploy is recovered.
- Good: a failure section by stage, from "commit a fix to `main` and rerun it manually" to "the release
  can't be fully reverted at this point".

**Missing recovery where a release can stop half done.** Raise it only where a step can fail after something
that cannot be withdrawn was published (a registry version, a pulled image, an immutable GitHub release) and
the text is silent on that state; raise it as a question for the maintainers, never with a recovery you
reasoned out. Raise nothing where the irreversible publish runs last after a dry run, where the project's
files name a release team or rotation that handles failed releases, or where it points to a recovery runbook.

## Policy the project has not settled

**Questions, not decisions.** Unsettled policy (when a release counts as done, whether a bad tag may move,
minor-versus-patch boundaries) is a question for the maintainers, never a request to the author; recovery is
under Recovery. Do not raise as missing what the PR description lists as left for the maintainers. Where the
linked issue or the PR description asks for a section (all three bump levels), its absence is a gap; a
proposal flagged in the PR description meets it, so raise nothing against it. A requirement with no source
("Merge it to `master` once it is reviewed and CI passes" where nothing requires review) is a decision; raise
it.

- Verify: trace each rule to a project file, workflow, setting, the linked issue or the PR description.

## What stays out of the file

**Verification stamps and this change's story.** How a fact was chosen or verified, and what this change
replaced, go in the commit message. For change narration, see docs-patterns.

- Prevents: text that ages ("(it is `toxiproxy_<version>_linux_amd64.deb` as of v2.12.0)").
- Raise nothing on version-stamped facts about older releases ("Releases before 2.0 used calendar
  versions"), a labelled fallback process, the reason for a release cadence, or a leftover outside the
  repository, which is a check ("If PyPI still names `publish.yml`, change it to `release.yml`").

**Point, don't restate.** How consumers update and pin belongs in the README or user docs; what every change
owes (regenerated files, a changelog entry) in CONTRIBUTING.md; what users may rely on in the project's
declaration of it; under a curated changelog, what an entry says in the changelog's rules. A value a file
declares (a dependency range, a minimum toolchain version) is pointed to.

- Prevents: two accounts drifting apart.
- Verify: grep the other files for the restated text; compare any quoted value with its manifest.
- Bad: "`app` declares `lib` (`^1.2.0`)". Better: "`app`'s supported `lib` range is in `app/package.json`."
- Raise nothing on release notes written or edited at release time (a blurb, a blog post, edited generated
  notes), release-time changelog chores (renaming `## Unreleased`), or user policy on a release page the docs
  site renders (supported versions).

## Changes that touch the release machinery

**Steps against the changed machinery.** When a change to the release document comes with workflow,
tag-pattern, publish-job or version-rule changes, check every step against them (the text's tag pattern
against the workflow's `on.push.tags` filter), including lines the diff leaves alone. A step the change makes
wrong is Important, or Critical as under Steps and commands.
