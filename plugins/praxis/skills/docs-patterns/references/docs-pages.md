# Reviewing docs page changes

Checks for a change to a page under `docs/` or on a docs site: how-to, reference, explanation and tutorial pages,
runbooks, operator guides, architecture pages and the home page. Where the project's own rules, checks or tools decide a point, raise
nothing against them. First review against the lines of `docs-pages.md` in the docs-patterns skill folder (beside
SKILL.md, not this file under `references/`), then apply these checks. Unless the PR's purpose is to write or rewrite
the page, raise only what the change adds or makes false. A wrong migration, upgrade, removal, recovery or rollback step
is Critical; an ordinary mismatch between the page and the code is Important.

## What the install runs

**Unreleased behaviour shown as current.** A reader on the released version configures a setting that does not exist
or skips an upgrade step that applies to them: Important, or Critical where it hides an upgrade or migration step from
readers on the released version. Raise nothing where the docs are built per version, say they describe the default
branch, or the install steps build from it, or the project has no release. A version mark must come from the tree or the release record. Verify: find
the release the install steps give: the image tag the compose file pulls, the package index, else the newest release of this
page's component (`gh release list --exclude-drafts --exclude-pre-releases`, or the newest `git tag --list
'<package>*' --sort=-v:refname` tag with no pre-release part, where tags carry a package name); each line the change adds must hold for it or carry its
version or "unreleased". Anything the changelog still lists under its unreleased section and the page documents
unmarked is a finding. Search the added lines for "an earlier version", "a version that", "a version carrying", "now" and "no longer".

- Bad: "Servers started by a version carrying this guard refuse ..." Better: "Servers from 0.2.0 refuse ..."

## Names and planned state

**A name that does not exist.** Every file, module, setting and command the page names (placeholders, and names the line marks removed or renamed, with the version where the release check applies, aside) must exist at the change's
head (`git ls-files`, `git grep`), or the sentence or section naming it must say it is planned, with its issue: a
contributor otherwise builds against what is not there. Important. A single note at the top of the page does not mark
the lines below it.

- Bad: an architecture page listing 29 files under "the code follows this layout", 15 of them missing, after one
  "parts of this are not built yet" note.

## Pages that disagree

**Sibling pages and the README.** For each setting, default, command and file the change touches, search the docs pages (`docs/` or the docs site's source)
and the README; two pages saying different things send one reader wrong: Important, against whichever is wrong. A page
that points to the other instead of restating it raises nothing.

**A stated procedure against the record.** A release procedure on a docs page is checked and tiered as
`references/releasing.md` does. A sync or deploy step the page states must match the forge (`gh run list -w
<workflow>` and the workflow's `on:`): Important where it does not, or Critical where following it deploys or publishes
something that cannot be taken back, as `references/releasing.md` tiers it.

## Steps

**Order and gaps.** A check that decides whether to go on must come before the step it guards, and an action another
page requires of this task's reader must be in the steps or linked from them; otherwise the reader acts before they
know, or misses the action: Important, or Critical for a migration, upgrade, removal, recovery or rollback step. Verify: search the
sibling pages for "before", "must" and "run ... first".

- Bad: a fork guide that checks for breaking `.env` changes after the merge and cleanup.

**A runbook that does not undo its containment.** Each containment step has a matching undo, or the page says why
none is needed (a scenario with no containment needs no undo): Critical where leaving it in place keeps users broken or unprotected, else Important.

## Generated reference

**Surface beyond the supported one.** A generated reference that includes internals without labelling them internal invites readers to depend on
them: Minor, or Important where the project states a public surface the reference contradicts. Verify: compare the
generator's targets (`automodule`, `:undoc-members:`, an include list) with the project's stated surface (README,
`__all__`).

## What not to raise

Raise nothing on a page another docs-patterns file covers (a changelog page), on adopter instructions in a template that are marked at their site, or on placeholders an adopter replaces, on a fragment a generator appends
to a README, on a page type the project does not keep, or on a page's departure from the existing pages where those
pages break a rule in docs-patterns, plain-writing or information-placement.
