# Where each kind of information goes

Default homes. A project rule moves any of them. "The commit message" means the text the merge
setting lands: every commit message on the branch under GitHub's default squash merge, which holds
unless the project's agent instruction files or CONTRIBUTING state another setting. Where a home does not exist in the project, use the
fallback the row gives, or the commit message where it gives none. Create a document type the project
does not keep only with the user's approval. A reviewer who finds the project needs one, or cannot
tell whether it keeps one, raises it once, as a Minor question for the user, not as an entry the
change is missing.

## For users and consumers

| Information | Home | Elsewhere, at most | Never |
|---|---|---|---|
| What the project is, who it is for, its status for the version a reader can install | README opening; a component's own README | one-line copies where a link cannot be followed: manifest and repository description, package-index page | CONTRIBUTING, RELEASING, a changelog header |
| What consumers may rely on (names, flags, outputs, tags) and how stable it is | once: in code where the language enforces it, else one README line | the changelog header, CONTRIBUTING, RELEASING and agent files point to it | the same surface reworded in several files |
| First use: prerequisites, the steps to one working result, how to tell it worked | README quickstart | a docs how-to for other install paths | mixed with contributor setup |
| Later tasks: configure, upgrade, remove, extend | a docs how-to page; README sections when there are no user docs; a component's install and removal in its README | a README pointer | only in a PR description, issue comment or RELEASING |
| Reference facts: options, defaults, environment variables, messages and what to do about them | the source the tool reads or prints (`--help`, a schema, generated reference), else a docs reference page; a README table when the surface is small | pages link that source | a hand copy of a generated fact; history in a table cell; one fact listed twice |
| How it works, as far as a user needs it | a docs explanation page; a README section when there are no user docs | one README line | root README "implementation details" that change nothing a user does |
| Limits: what it does not do or defend against, by decision | where the user decides or meets it: a README caveat, a limitations page, the docstring at the call | a changelog entry when a release changes one; a one-line PR flag | only in a PR description |
| What a call means beyond its signature: edge cases, failure, call order | the symbol's docstring | reference generated from it | types or defaults restated where the signature is annotated (unless the project's docstring style requires them); an undecided plan (a decided deprecation or removal version is fine); history; maintainer rationale on a rendered surface |

## Change records

| Information | Home | Elsewhere, at most | Never |
|---|---|---|---|
| A change a consumer sees: behaviour, breaking change, removal, deprecation, fix | the changelog entry for the version that ships it, written in the same change | release notes made from it; a breaking mark on the commit message only when the change breaks something consumers rely on, in the form the project's release tool reads; a one-line PR flag | internals, CI or tests outside a section the changelog keeps for them, or rationale and process that change nothing a user does, in the changelog; the PR description as its home |
| What a consumer or operator must do to upgrade, for an action this change makes necessary | the changelog entry for the version that needs it | a docs migration page when long; the release notes | only in the PR description; only in the commit message where the project keeps a changelog |
| A security fix, after its release | the changelog's security entry; the advisory | the release notes | before the release, anything beyond what the vulnerability row allows |
| The change, in one line | the PR title, which becomes the squash commit's subject for a PR with two or more commits (a one-commit PR lands its commit's subject) | | "address review", "round 2", two changes joined by "and", branch names |
| Why the change was made: the problem, the cause, the approach over named alternatives, accepted costs, why a dependency was added, versions verified against | the commit message | the PR description gives the intent and the why in a sentence or two; a document carries at most a one-clause reason that changes what its reader does | reasons in the changelog that change nothing a user does; code comments, except a reason an editor at the line needs |
| A decision with its alternatives and evidence | the commit message of the deciding change, or the project's decision record | the issue keeps the discussion; a rule that follows from it points to it | README, CONTRIBUTING or RELEASING bodies |
| Something contributors must do once after pulling (rebuild the dev container) | the first paragraph of the commit message that makes the change, with no breaking mark; under a squash merge it stays there, wherever that message falls in the squash | a one-line PR flag; CONTRIBUTING when it recurs | the changelog; the PR description as its only home |
| Authorship, co-authors, sign-off | trailers on the commit message | the project's AI-contribution policy in CONTRIBUTING | prose bylines in files; persona or agent names in prose (trailers are this row's home) |

## For the reviewer and the merger

| Information | Home | Elsewhere, at most | Never |
|---|---|---|---|
| Intent, and flags for what the diff alone would let a reviewer misjudge | the PR description | | file inventories; a retelling of the commit messages beyond the opening what-and-why and the flag and decision lines with their reasons; process narration; raw tool output; template skeletons |
| Verification: what ran and what it showed, what was not run | the PR description; the commit message when there is no PR | the commit message keeps the versions verified against; results a commit message already states need no copy in the PR description | test docstrings; docs; raw output (link the run); totals CI already shows |
| Where to start reading | the PR description, except where the merge setting lands it | | a PR comment |
| Merge conditions and what merging sets off | the PR description, as facts that stay true ("Requires #52.", "Merging publishes 0.3.0.") | RELEASING holds the standing sequence | merge-status narration ("not merging yet") |
| Review findings | the review, where whoever asked for it reads it | | praise; vulnerability detail the vulnerability row bars |
| Answers to findings | the fix; a decision a reviewer might question, a declined finding included, as a PR description flag with its reason | a reply on the PR to a finding a person posted that was declined, fixed differently or found already the case, in its thread when it was posted on a line; a lasting reason goes to its own home and the reply points there | commit messages as the answer; "changed in review" or "declined from review" lines; a reply per round or per fixed finding |

## In the code

| Information | Home | Elsewhere, at most | Never |
|---|---|---|---|
| Why a line has its shape: a constraint, a hidden hazard, a rejected alternative an editor would retry, sites that must change with it | a comment at the site, with the condition or decided version that ends the constraint ("removed in 3.0, see #58"), or a test that pins it | the commit message gives the change-level reason; for a format without comments, the commit message | only in a PR description, review reply or commit message when an editor at the line would break it unaware; README; docs |
| What a file is, owns and does not; whether it is generated or copied and where to edit it | the file header (module docstring or leading comment block) | CONTRIBUTING states the generated-file rule once | indexes and listings; history; bylines |
| Origin and licence of copied code | the copied file's header: origin and licence id | the importing commit's message says why; a README credits line | prose bylines |
| What a test guards, and how its expected values are regenerated | the test's docstring or name | | a tracker id in place of what the test guards; people's names; proof that it failed before the change (that is the PR's) |
| A rule a future change must obey | the home nearest whoever would break it: the site comment (one site), the file header (one file), a component's own README (files in one component), an architecture page (several components), CONTRIBUTING (contributing), RELEASING (releasing); with one clause of reason | the reasoning in the deciding commit message or decision record | a PR description or issue thread as its only home; design sections in the root README |
| Architecture: the parts, their boundaries, rules a change is checked against | each component's own README, where components have READMEs apart from the root one, for its parts and boundaries; a docs architecture page that the agent file or CONTRIBUTING points to, where the project keeps one, for how the components fit; without either, package headers | one root README line | the root README's body; tree listings; a target design written as present |

## Project process

| Information | Home | Elsewhere, at most | Never |
|---|---|---|---|
| Contributor setup, the checks to pass, conventions | CONTRIBUTING; the agent file when the project is solo with one agent harness; a README Development section where the project has no CONTRIBUTING | the agent file gives one-line triggers and pointers; README points to CONTRIBUTING | the full rule restated in README, agent files and RELEASING; the full CI check list |
| Release steps and recovery | one release document (RELEASING, or a CONTRIBUTING section in a small project), with recovery in a runbook it points to | an agent-file trigger ("a change under X needs a version bump: see RELEASING") | PR descriptions as its only record; the changelog |
| Maintainer chores: lint-hook upkeep, upstream or template sync | a maintaining section in CONTRIBUTING, or a maintainer page outside the user docs; a README Development section where the project has no CONTRIBUTING | | the user docs site |
| How to report a vulnerability | SECURITY.md, or the owner's default | CONTRIBUTING, README and the issue chooser point to it | vulnerability detail |
| Template-adopter instructions | a marker at the site addressed to the adoption step | | anything that survives adoption |

## Planning and status

| Information | Home | Elsewhere, at most | Never |
|---|---|---|---|
| The problem, its scope and constraints, each place it shows | the issue body, edited to stay current | the commit message states the problem in a sentence; the PR description links the issue | a scope change recorded only in a comment; "as decided on #N" without the decision |
| The plan | the author's workspace | the PR description flags departures | a restatement of the issue; a plan comment nobody asked for |
| Working notes: a fix's step-by-step checklist, `file:line` pointers for a fix, files to touch | the author's workspace, never a shared home | | the issue, a posted plan, the PR |
| Findings during the work | the author's workspace; a finding that moves scope is edited into the issue body | the commit message carries the evidence that decided the shipped design | an issue comment per finding |
| Why an issue closed with no change | one comment when closing it | | |
| Deferred work, known defects | an issue per item | `TODO(#N)` at the site; "Deferred: #N" in the PR description or reply; a PR-description flag naming a defect the change found and left, until it is filed; a planned state in a document, marked as planned and linked to its issue | "the next PR"; undecided version-tied plans in docstrings |
| Status: opened, merged, blocked, released | the forge's own state: issue and PR state, closing links, labels, tags | a comment only for "released in vX" to an outside filer, which the forge does not show; in a document, a version or "unreleased" mark on behaviour newer than the installed release | status in docs, code, commit messages or PR descriptions |
| Detail of a vulnerability whose fix is not released | the private channel SECURITY.md names | public text describes the fix neutrally; the commit message whose diff removes the flaw, and text that links the released fix or a public advisory, may describe it | an issue, branch name, other commit message, PR, review, code comment or unreleased changelog section in a public repository, unless it links the released fix or a public advisory |

## Nowhere

| Information | Exceptions |
|---|---|
| How the work went: rounds, agents, timings, CI re-runs, the debugging story | a review reply and an issue or plan comment, read in the moment, may narrate |
| Restated or derived content: change inventories, diffstats, counts CI or the code already shows, the signature, indexes, empty form sections, boilerplate, praise | a list whose items each give a reason; public names a change removes (what a later reader would search for); generated, drift-checked copies; measurements stated with their conditions |
