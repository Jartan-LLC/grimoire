# Reviewing contributing changes

Checks for a change to a contributor guide (CONTRIBUTING.md or its `.rst` form, wherever GitHub shows it: `.github/`,
the root, `docs/`, or the owner's `.github` repository). Where the project's own rules, checks or tools decide a point,
raise nothing against them. First review against the lines of `contributing.md` in the docs-patterns skill folder
(beside SKILL.md, not this file under `references/`), then apply these checks. Unless the PR's purpose is to write or
rewrite the guide, not a code change that also edits it, raise only what the change adds or makes false.

## Rules the project has not adopted

**Rule sources.** Find the source of each rule, channel or promise the change adds; without one, contributors act on a
policy nobody runs ("The maintainer reviews every pull request"). Verify: search the tree, the task and linked issue,
the PR description, the owner's `.github` repository and the forge's settings (`gh api repos/OWNER/REPO`,
`gh api repos/OWNER/REPO/rulesets`). Raise an AI policy, CLA or code of conduct the project has not adopted. A rule a
tool or forge setting enforces is a fact worth stating, not an invention: pacman does not upgrade an installed package
unless `pkgver` or `pkgrel` rises; a GitHub setting can cap each contributor's open PRs.

**Security route.** A line the change adds or edits that sends security reports to a public issue discloses the flaw
before a fix exists: Critical. A pointer to a missing SECURITY.md or address is Important. Verify:
`SECURITY.md` or `.github/SECURITY.md`, `gh api repos/OWNER/.github/contents/SECURITY.md` for the owner default, and
`gh api repos/OWNER/REPO/private-vulnerability-reporting`.

**Rule changes not flagged.** A change that adds or alters a contributor rule should say so in the PR description, or
reviewers merge a policy change unnoticed. Verify: find each rule the diff adds or changes in the
PR description. A written rule that recent history ignores stays; the PR names the conflict instead of deleting it.

**A guide nobody asked for.** Creating a CONTRIBUTING.md where none exists, unless the task, a linked issue or the
user's approval stated in the PR description asks for one, is a finding; so is editing a file GitHub does not show while another is shown (a root CONTRIBUTING.md beside
`.github/CONTRIBUTING.md`). Contributors then read a guide other than the one changed. Verify: list each location above.

## What a change owes

**Obligations without a trigger.** For each by-hand obligation a change can trigger (a version bump, a changelog entry,
regenerated files, what the PR must state, steps to add a component), the guide should give the trigger, the action and
where detail lives; a contributor who misses one gets a failed review or a broken release. Verify: list the obligations
from the release workflow, version fields, generators and changelog, then find each in the guide.

- Bad: "Update the changelog."
- Better (bat): an entry for behavior, syntax-mapping or theme changes; none for docs or typo fixes.

A non-obligation counts too ("manual pages for commands will automatically get updated"). Where the project takes
patches by email or through Gerrit, so reviewers read the commit message, the guide says what it must state.

## Setup and the local check

**Setup that stops short.** The setup the guide gives or points to should take a fresh clone to a passing check: each
command, what it installs, when to rerun it ("rerun it after dependencies change"), and prerequisites it leaves out.
Otherwise the first check fails unexplained. Verify: walk the commands against the Makefile, package manifest or dev
container. Where nothing must be installed (a content-only repository such as github/gitignore), raise nothing.

**Copied versions and machine facts.** A minimum version copied by hand from a file that pins it is true today and stale
after the next bump; so are timings and "the newest supported version". Verify against the pin: `package.json`
`engines` or `packageManager`, `requires-python`, `cmake_minimum_required`, `rust-toolchain.toml`.

- Better (vite): "You can find the required pnpm version in `package.json` under the `packageManager` key."

A minimum the tree does not declare is not a copy; raise nothing. A copy already false is a false claim (below).

**The check command.** The guide should name the local command closest to CI's checks, with the environment CI sets for
it, and point to the workflow for the rest instead of listing jobs or version matrices, which go stale. Verify: compare
with the CI workflow. Without CI, the local check alone; without any check, raise nothing.

- Bad: a docs build command without `READTHEDOCS=True` when CI's docs job sets it.
- Better: "`make check` runs the lint and tests CI runs. CI runs more (see the workflow)."

**Claims against the tree.** Every command, path, version and CI claim must hold in the tree the change leaves; a
false one is Important: babel's "Travis CI runs the tests" with no `.travis.yml`; googletest's "CMake v2.8.12 or newer"
while `CMakeLists.txt` requires 3.16. Verify: run or read each. "Must pass before merge" needs branch protection, which
the tree does not show: check `gh api repos/OWNER/REPO/rules/branches/BRANCH` or
`gh api repos/OWNER/REPO/branches/BRANCH/protection`; if neither is readable, report the claim as suspected.

## Traps

**Missing or wrong warnings.** Look for a command or habit that damages real data or shared state, or fails confusingly
here, with no warning saying what happens and the safe way. Verify: read test fixtures, scripts and hooks for writes
outside the checkout (Docker volumes, a shared daemon, real config).

- Better (attrs): uncheck "Copy the main branch only" when forking, or the tests fail for want of Git tags.

A warning the change adds or edits whose safe way is wrong, or a missing warning on a data-destroying command the
change adds or edits, is Critical; an unwarned command outside the change is a note, not a blocker. A failure from a
defect is an issue first: at most an interim warning naming it, not a permanent "unsupported on Windows" line.

## One home per rule

**Restated rules.** Each rule lives once; other files point by file and topic ("Bump levels: RELEASING.md"). A
condition or action retold in the README or a second guide drifts on the next change. Verify: grep the tree for the
rule's key words. Release steps belong in the release document where one exists. In an agent file the change edits, a
multi-line copy of a CONTRIBUTING.md recipe is the failure. A line correcting an inherited template line to match the
project's policy file, with a pointer there, is no restatement unless it retells more than the corrected point. A
translation is a copy on purpose; raise only a rule changed in one language and not the others.

## What stays out

**Rules that bind nothing yet.** Each instruction should serve a change possible today, or contributors follow steps
for code that does not exist. A spec for unbuilt work (a runner table, wiring "to add with the first tests") belongs in
an open issue; how a decision was reached belongs in its commit message, or the decision record where the project keeps
one. Verify: search the tree for each runner, file or target a rule names.

**Overviews and internals.** An architecture tour, or internals the code or a Makefile header states, costs time on a
page read for a task. A page that only links to each area's own guide is a pointer, not an overview.

**Length.** Length is a finding only through the checks above. The guide's existing tone and welcome lines are the
project's voice. A thank-you or welcome a change adds where the guide had none is filler (Minor).

## Outside contributors

Where outsiders open PRs or issues, the guide should say when to ask before starting work, or an outsider spends days on
a change the maintainers decline. Verify the condition:
`gh api 'repos/OWNER/REPO/issues?state=all&per_page=100' --jq '.[].author_association'` lists PRs and issues; an author
other than OWNER, MEMBER or COLLABORATOR is an outsider.

- Better (uv): "Please do not open pull requests for new features without prior discussion."

Where issue forms exist, a pointer covers bug reports. A project that takes no outside changes says so and where reports
go. In a private repository other teams are outsiders: these checks apply. A turnaround the team has set belongs in the
guide; one nobody set is an invented policy.

## Templates and rendering

**Unmarked template lines.** In a template repository (`gh repo view --json isTemplate`), each line a derived repository
must change or delete should be marked, in the guide or the template's setup step, or the setup step says the whole
file is replaced; otherwise derived repositories inherit a false CI or setup claim.

**Template syncs.** In a guide synced from a template, read each inherited line against the project's policy and setup
files, or contributors follow the template's policy. A hedged line that "holds under both" still fails if it allows
what a project file forbids; a true project-specific line or pointer the sync removed is a finding.

**Links where the file renders.** If a docs site includes the guide (pytest's `.. include:: ../../CONTRIBUTING.rst`),
its links must resolve there too; a repository-relative link breaks on the site.
