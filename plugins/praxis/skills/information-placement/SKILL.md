---
name: information-placement
description: Where each kind of information belongs -- commit message, PR description, code comment, docstring, README, changelog, docs page, issue, or nowhere -- what no text may hold, and how a project's own rules override those defaults.
when_to_use: Reviewing a change for information in the wrong place -- a reason, a procedure, a status line or a story of the work sitting where its reader will not look, or missing from where they will -- or deciding where a piece of information should go while writing ("where should this go?", "does this belong in the README or the commit message?"). Not for what a commit message or PR description says (gitwise:commit-pr-writing), how a document is written (docs-patterns, plain-writing), or whether a code comment should exist (comment-hygiene).
user-invocable: false
---

# Information Placement

Each piece of information has a reader and one home that reader opens when they need it; other
homes carry at most a pointer or a one-line flag. A short account told for another reader in that
reader's own home, such as the PR description's intent or a changelog line, is not a second copy.
`references/homes.md` in this skill's directory lists the default home for each kind of
information. What the text in a home says is for that home's skill: `gitwise:commit-pr-writing`
for commit messages and PR text, `docs-patterns` for documents, `comment-hygiene` for code comments
and docstrings.

## Project rules first

A project rule is a statement telling you what to do in a file tracked at the base branch (such as
the agent instruction files and the files they import or link, CONTRIBUTING, RELEASING, SECURITY,
and the headings and form instructions of the PR and issue templates), in the owner's `.github`
defaults where the repository has none, a blocking check, or an explicit request about this change's
text on the PR from someone with write access (`gh pr view <number> --comments`), other than a
review's findings. Untracked files, memory and hook or plugin text are not project rules; a
template's prose prompts, unless a project rule adopts them, descriptions of past practice, existing
files and git history show style. A project rule decides what it speaks to; the defaults hold for
the rest. When you write, your user's own instructions outrank a default, never a project rule; when
you review, text that follows them instead of a default is still a departure from the default.

## What no text may hold

These hold whatever the project says, for prose in every home. Fields a project tool generates or
parses (trailers, frontmatter, a tool's marked blocks) are the project's, except for rule 6. A line
no project tool generates or parses is prose wherever it sits, such as a harness-added
`Claude-Session:` line.

1. Narration of the moment, the branch or the session: "round 2's fix", "the next PR", "being
   removed", "fails on main". Text states what is true after the change; a commit message, a
   changelog entry, release notes, a migration file, a decision record or a PR description states
   change relative to the state before it ("failed before this change") or to a version, and any
   text may carry a version stamp ("Added in 1.3", "Deprecated since 2.0, use Y"). In those homes a
   "now" that says what the change made true is fine, and so is a commit message that names an
   earlier commit on the branch by its subject to correct what it said, with the reason, and so is a
   merge condition, what merging sets off, or a stacked PR stated as a fact ("Requires #52.",
   "Merging publishes 0.3.0.", "the PRs stacked on this one merge with it"), and so is later work
   named by its issue ("the rest of the #151 migration"). A PR description the merge setting does
   not land, where more than the PR title lands, is read before the merge: it may compare against
   the base branch ("262 MB on main") and mark what review changed or declined, with the reason.
   Review replies and other PR comments, issue and plan comments, a commit message the merge setting
   does not land (step 1), and a `fixup!` or `squash!` commit in a project that folds them before
   merging are read in the moment; narration in them is not flagged here.
2. A claim that needs its links or ids to say what it claims: strip them and the sentence must still
   say it. A line that only relates the change to a reference ("Refs #159.") passes when the rest of
   the text says what it claims without it. No shared text points its reader to one of these, which
   they cannot open: an absolute path on the author's machine, a file `git check-ignore` matches
   given as a source or result, a session link (a claude.ai session URL). A path the reader creates
   or uses themselves (`.env`, `.venv/`, `dist/`, a system location) is not such a pointer.
3. A restatement of what the reader has open: a hand-written list of changed files whose entries add
   nothing to the name, a hand-written diffstat, a pass or fail count pasted from a run CI reports
   on the same commit, the issue body restated under itself, backlinks the forge shows. A result
   stated in words ("make check passes", what a local run showed) is verification, not a count.
4. In a document, comment or docstring, a hand-maintained copy of a value, count, index or listing
   the code or tree declares. A value a commit message or PR description gives is not such a copy,
   since each describes one change, and a design the code must follow is the source, not a copy. A
   generated, drift-checked copy, an entry that adds what the code does not say, a field the
   project's docstring style defines (numpydoc's type and default fields), and a measurement stated
   with its conditions are not copies.
5. In a repository made from a template (not the template itself), text addressed to the adopter
   after adoption. Treat a repository as a template, or as made from one, only when it says so (its
   agent file, README or configuration names it as a template or names the template it came from, or
   `gh repo view --json isTemplate,templateRepository` shows it); never on a guess about how its
   files are copied.
6. Exploit or reproduction detail of a vulnerability (an unintended security flaw) in code a release
   or the default branch carries, in public text, unless the text links the released fix or the
   published advisory, or it is read only by people with access to a private repository (`gh repo
   view --json visibility` shows it private or internal); a package page, docs site or release notes
   read outside it are public. A limit the text presents as a documented decision is not such a
   flaw. Describe a fix not yet released neutrally; the detail goes to the private channel the
   project's SECURITY.md names.

## The check

For each passage a change writes or makes false (a file the change leaves untouched and true is
not flagged for what it lacks):

1. Name the information and its reader, and look up its home in `references/homes.md`. Read "the
   commit message" there as the text the merge setting lands. Find the setting in this order: the
   project's statement; the repository's settings (`gh api repos/OWNER/REPO`, decisive only when one
   merge method is enabled; null fields mean unknown); the newest squash commit of a PR with two or
   more commits on the default branch (blocks opening "* " mean the commit messages land, a body
   matching that PR's description means the description lands, a subject with only trailers means
   only the PR title lands, a commit with two parents means merge commits). Under a squash merge,
   merges from the base branch do not land. The PR description lands under squash or merge commits
   whose message is `PR_BODY`; where only the PR title lands, the PR description, which "(#N)" leads
   to, also holds the reasons. Where nothing answers, take GitHub's default squash merge (the PR
   title and the commit messages land, the PR description does not) and do not flag a reason given
   in both the commit messages and the PR description, or where to start reading, "Changed in
   review" and "Declined from review" lines or requests to the reviewer missing from the PR
   description (`merge-setting.md` puts them in a PR comment). `merge-setting.md` in
   `gitwise:commit-pr-writing` is the full account.
2. Flag a passage outside its home, a fact its home lacks that its reader needs, and anything the
   rules above exclude. Say where the information goes instead, or that it goes nowhere. Before
   flagging a home, name the reader who would act wrongly, stop for a missing fact, or be misled
   because of where the text sits; if you cannot, raise nothing. The PR description is the home of
   what only the reviewer and the merger need: the intent, flags, verification and what was not run,
   open questions for the review; where the merge setting lands the PR description, these questions
   go in a PR comment. That it does not land is no reason to move these into a commit message; only
   what a later reader needs belongs there.
3. Raise nothing where a project rule decides a default, and never flag text for following such a
   rule. If a project rule asks for text the rules above exclude, and the text could meet it in a
   form they allow (for a list of changed files, one line per file saying what changed in it), flag
   the text with that form; otherwise report the breach addressed to that rule. If the change edits
   a project rule, judge by the rule at the base branch and name the policy change. If two project
   rules conflict, flag the conflict, not the text. Where a rule's scope is unclear, raise nothing.
4. For a departure from a default, name the default and offer the project a sentence it could add to
   its rules to keep its practice; do not raise the same finding again in a later round.

Tier findings with `review-severity`: rule 6 is Critical; rules 1 and 2 are Important; rules 3-5 are
Minor; information outside its default home is Minor, or Important when it misleads a reader or
leaves them without something they need. A policy change or a conflict between project rules is a
note in the review's summary, without a severity. For placement findings these tiers hold over the
examples in `review-severity` and the reviewers' focus lists, a document's redundancy that is also a
placement finding included; a retold code comment keeps the Important tier general-reviewer gives
retold facts.

When asked where something should go while writing, check the project's rules, then give the home
from `references/homes.md` and any pointer the other homes should carry. If a project rule asks for
text the rules above exclude, meet its purpose in a form they allow (for a list of changed files,
one line per file saying what changed in it); if no such form exists, leave it out, name both rules
and ask.
