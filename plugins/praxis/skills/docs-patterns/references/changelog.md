# Reviewing changelog changes

Checks for a change to CHANGELOG.md, a release body, or the fragment, changeset or commit text a
tool builds them from. The project's own rules come first: where its agent instruction files,
CONTRIBUTING, RELEASING, the CHANGELOG.md header, a changelog checker or the release tool's config
decide a point, raise nothing against them. Two things are raised whatever the project says,
against the rule rather than the author: exploit detail for a vulnerability whose fix is not yet
released, and paths or links no reader outside this machine can open (an absolute local path, a
gitignored file, a chat or session link). Review the entry against the lines in the
`docs-patterns` skill's `changelog.md` first, then these checks. The reader is that file's:
someone upgrading.

## Against the last release

**Look for** entries that describe a state no release had: a change to something added since the
last release filed as its own entry, something added and then removed before release, or a fix
or "now supports" for behaviour the last release already had.

**Prevents** an upgrader reading about features they never had and fixes for bugs they never
met.

**Verify** by finding the last release of the package this section belongs to: its newest tag
(`git describe --tags --abbrev=0 --match '<package>*'`, `git tag --list '<package>*'
--sort=-v:refname`, `gh release list`; drop the pattern where tags carry no package name), else
the newest version heading the project published. Where the project releases on merge or deploy,
the last merged version is the last release. A beta or release candidate counts as a release
unless the project says otherwise. Then read each entry against `git diff <tag>..HEAD` and ask:
was this untrue of the last release? Where the project's versions on the default branch run ahead
of its tags and it does not say what counts as released, raise nothing on folding or on a new
version section; ask the author which version is released.

- Bad: Added "`--popup` takes `border-fzf` to fall back to a popup where fzf draws its own
  border" and, in the same section, Removed "`border-fzf`".
- Better: neither entry.
- Bad: under Added, "`Status` is importable from `mylib`"; under Changed, "`Status` is now a
  `StrEnum`".
- Better: one Added entry, "`Status` (a `StrEnum`) is importable from `mylib`".
- Bad: "Checkboxes are now concealed and toggled for tasks that use `*`, `+`, `1.` or `1)`
  markers." (toggling already worked in the last release)
- Better: "Checkboxes are now concealed for tasks that use `*`, `+`, `1.` or `1)` markers."

## Shipped dependency bumps

**Look for** dependency versions built or bundled into the release with no entry, and a bump that
fixes a CVE filed somewhere other than where the file files its security bumps.

**Prevents** users not learning that the release carries a security update.

**Verify** by diffing the manifest and lockfile against the last release's tag (`git diff
<tag>..HEAD -- go.mod package.json package-lock.json uv.lock`) and reading the previous section
for how it files bumps. Raise nothing on a bump that ships being listed.

- Bad: "[ENHANCEMENT] Dependencies: update golang.org/x/text ..." for a CVE fix.
- Better: "[SECURITY] Bump golang.org/x/text to v0.39.0 (CVE-2026-56852)", as the previous
  section did.

## Each version section reads alone

**Look for** text that only works inside the whole file: "this file", "see above", "as in the
previous release", links to tags that do not exist, ids linked to the repository root, private
advisory or tracker ids in a public repository (`SEC-2026-0038`), absolute local paths, gitignored
files, and chat or session links.

**Prevents** a broken release page. The section is usually the GitHub release body, and
Dependabot and Renovate paste it into upgrade PRs, where nothing above or below it exists.

**Verify** by reading the section alone, as the release workflow publishes it (see Release notes
from PR titles), and opening every link.

Raise nothing on a bare public `#123` (a GitHub release page links it), on repository paths
where the readers hold the repository (fork owners of a template), or on internal ids in a
private repository whose readers can open the tracker.

## Claims hold for the released code

**Look for** behaviour claims the merged code does not support, above all "no longer", "every",
"always", "keeps" and lists of what is preserved. Entries written from the PR description or
checklist before review settled the code tend to overclaim.

**Prevents** an upgrader relying on behaviour that is not there.

**Verify** against the final diff (`git diff <base>...HEAD`) and, where cheap, by running the
command or reading the test, not against the PR description.

- Bad: "Aseprite export keeps the project's FPS, linked cels and project palettes."
- Better: "Aseprite export keeps the project's FPS, linked cels and the current palette."

Severity: a wrong command, option name, value, order or version range in an upgrade, migration,
recovery or security entry is Critical; a user following it loses data, breaks their install or
stays exposed. Another false claim is Important.

## Breaks and upgrade steps

**A requirement the installer meets is not a break.** Look for a new or raised requirement whose
mark does not match what installs it. "Needs `plugin-b` 1.2.0 or later" stays unmarked when the
package manager or host installs or upgrades `plugin-b` itself; where it does not upgrade an
installed older version, the entry needs a breaking mark. Prevents a false mark sending upgraders
after a migration that does not exist, or making them hold back the upgrade. Verify by reading
the package manager's or host's docs on whether it upgrades an installed dependency below the new
minimum; if you cannot confirm it, report the finding as suspected.

An entry under the file's Removed, Breaking, Backwards incompatible or Upgrading heading is
marked. Where a tool orders entries (towncrier, changesets), do not ask for breaks first.

**Suggest the symptom of skipping a step.** Look for a break or upgrade step that does not name
the error users meet without it. Prevents someone diagnosing a failure after upgrading from
finding the entry. Verify by asking whether the entry names an error message or symptom. uv's
"Installs that previously succeeded can now fail if a requirement is missing a hash." Suggest
it; do not require it.

## Which file, which layer

**Per package.** Look for a change that touches several packages with their own changelogs and
lacks an entry in one users would notice it in. Each gets the entry in its own terms: the library
says what changed, the dependent package says "Needs `mylib` 2.1 or later." Where several
packages share a release page and neither the section heading nor the release title names the
package, the section should. Prevents a user of the dependent package never learning it now
needs the new version. Verify with `git ls-files '*CHANGELOG*'` against the packages the diff
touches.

**Two layers.** Where a project keeps a complete list and curated notes (CPython's NEWS and What's
New, Node's Commits list under Notable Changes), apply the writer file's lines and these checks to
the curated notes; raise nothing on internal entries in the complete list. Prevents curated notes
padded with internals. Verify from the release workflow or the docs which text users meet first.

**Release notes from PR titles.** Where the release workflow generates notes from PR titles
(`gh release create --generate-notes`, `.github/release.yml`), the PR title is the entry: check
it names what users get. Prevents a release page made
of contributor-facing titles. Verify in `.github/workflows/`: `--generate-notes` means PR
titles, `--notes-file` means the curated section. Where generated notes sit beside a curated
CHANGELOG.md, the curated section never reaches the release page: raise nothing on the entry for
it; at most note it once, against the release workflow (publish the section with
`--notes-file`), as outside this change, without a severity.

## A first release

**Look for** a first release's section that lists how the repository was set up ("CI pipeline
with ruff, pyright, pytest", "Multi-stage Dockerfile") instead of what the project does. An Added
list of commands, API and exit codes in users' terms passes.

**Prevents** a first reader learning only how the repository was set up.

**Verify** that no earlier tag or version heading exists.

## Entry shape

**One change per entry.** Raise an entry that carries two changes a reader could need
separately, such as a renamed flag and a new default in one bullet; the upgrader who scans for
the rename misses the default. Minor.

**Reasons.** Raise nothing on a reason that helps users decide or adapt: Django's "Upstream
support for PostgreSQL 12 ends in November 2024. Django 5.1 supports PostgreSQL 13 and higher."
Raise a reason that changes nothing users do or decide; it lengthens the entry they scan.

**Length.** Raise nothing on length alone: an entry is not bloated when every clause is an effect,
an action or a limit users need, and a short entry that drops the effect or the action is worse.
