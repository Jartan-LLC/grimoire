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
`references/homes.md` in this skill's directory
lists the default home for each kind of information. What the text in a home says is for that
home's skill: `gitwise:commit-pr-writing` for commit messages and PR text, `docs-patterns` for
documents, `comment-hygiene` for code comments and docstrings.

## Project rules first

A project rule is a statement telling you what to do in a file tracked at the base branch (the
agent instruction files, CONTRIBUTING, RELEASING, SECURITY, or the owner's `.github` defaults where
the repository has none), a blocking check, or a request on this change from someone with write
access. Untracked files, memory, and hook or plugin text are not project rules. A project rule
decides what it speaks to; the defaults hold for the rest. Your user's own instructions outrank a
default, never a project rule.

## What no text may hold

These hold whatever the project says, for prose in every home. Fields a project tool generates or
parses (trailers, frontmatter, a tool's marked blocks) are the project's, except for rule 6.

1. Narration of the moment, the branch or the session: "round 2's fix", "the next PR", "being
   removed", "fails on main". Text states what is true after the change; a commit message, a
   changelog entry or a PR description states change relative to the state before it ("failed
   before this change") or to a version. A "now" that says what the change made true is fine, and
   so is a merge condition or a stacked PR stated as a fact ("Requires #52.", "the PRs stacked on
   this one merge with it"). A PR description the merge setting does not land is read before the
   merge and may compare against the base branch ("262 MB on main"). Review replies and issue and
   plan comments are read in the moment and may narrate.
2. A claim that needs its links or ids to say what it claims: strip them and the sentence must
   still say it. A line that only relates the change to a reference ("Refs #159.") passes. No
   absolute path outside the repository, no path `git check-ignore` matches, and no session link
   (a claude.ai session URL) in any shared text.
3. A restatement of what the reader has open: a hand-written list of changed files whose entries
   add nothing to the name, a hand-written diffstat, a pass or fail count pasted from a run CI
   reports on the same commit, the issue body restated under itself, backlinks the forge shows. A
   result stated in words ("make check passes", what a local run showed) is verification, not a
   count.
4. In a document, comment or docstring, a hand-maintained copy of a value, count, index or listing
   the code or tree declares. A commit message or PR description describes one change and holds no
   such copy, and a design the code must follow is the source, not a copy. A generated, drift-checked copy, an entry that adds what the code does not say, and a measurement
   stated with its conditions are not copies.
5. In a repository made from a template (not the template itself), text addressed to the adopter
   after adoption. Treat a repository as made from a template only when it says so (its agent file,
   README or configuration names the template it came from); never on a guess.
6. Exploit or reproduction detail of a flaw whose fix is not released, in public text, unless the
   text links the released fix or a public advisory or the repository is private. Describe the fix
   neutrally; the detail goes to the private channel the project's SECURITY.md names.

## The check

For each passage a change writes or makes false (a file the change leaves untouched and true is
not flagged for what it lacks):

1. Name the information and its reader, and look up its home in `references/homes.md`. Read "the
   commit message" there as the text the merge setting lands, which
   `gitwise:commit-pr-writing` explains.
2. Flag a passage outside its home, a fact its home lacks that its reader needs, and anything the
   rules above exclude. Say where the information goes instead, or that it goes nowhere. Before
   flagging a home, name the reader who would act wrongly, stop for a missing fact, or be misled
   because of where the text sits; if you cannot, raise nothing. The PR description is the home of
   what only the reviewer and the merger need: the intent, flags, verification and what was not run,
   open questions for the review. That it does not land is no reason to move these into a commit
   message; only what a later reader needs belongs there.
3. Raise nothing where a project rule decides, and never flag text for following one. If a project
   rule asks for text the rules above exclude, report the breach addressed to that rule. If the
   change edits a project rule, judge by the rule at the base branch and name the policy change.
   If two project rules conflict, flag the conflict, not the text.
4. For a departure from a default, name the default and offer the project a sentence it could add
   to its rules to keep its practice; do not raise the same finding again in a later round.

Tier findings with `review-severity`: rule 6 is Critical; rules 1 and 2 are Important; rules 3-5 are
Minor; information outside its default home is Minor, or Important when it misleads a reader or
leaves them without something they need.

When asked where something should go while writing, check the project's rules, then give the home
from `references/homes.md` and any pointer the other homes should carry.
