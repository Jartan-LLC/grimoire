---
name: code-hygiene
description: Language-agnostic code hygiene — delete dead/duplicated/orphaned code, don't reinvent well-maintained solutions, keep comments describing state not change.
when_to_use: Writing or reviewing code, adding a solution that may already exist, removing code, or writing comments.
---

# Code Hygiene

Don't leave — or write — code that git or an existing solution already owns. Two failure modes: **zombie code** (dead, reinvented, orphaned, or bloated code) and **tombstone comments** (comments that narrate a change instead of describing current state). Both are cheap to introduce and easy to miss, especially in fast or AI-assisted work that outpaces comprehension.

## Tombstone Comments

A comment describes the code's current **state**. If it narrates the **change** that produced the code (what was removed, moved, renamed, or done "per review"), delete it — git owns change history. Such comments duplicate the diff, drift as the code evolves, and are meaningless to a reader who never saw the prior version.

Antecedent: Robert C. Martin, *Clean Code* (Ch. 4, "Comments") names the file-top changelog a **journal comment**, made redundant by source control. "Tombstone comment" (this project's coinage) generalizes that to any change-narrating comment.

**Core rule:** State, not transition. Current behavior or a non-obvious *why* → keep. The delta from the old version → delete.

**Decision logic (in order):**

1. **Cold-reader test** — would it make sense, and be worth writing, to a first-time reader who never saw the prior version or the PR? No → tombstone → delete.
2. **Git-ownership test** — does the fact it conveys amount to "what changed / moved / was removed"? That's version control's job → delete.
3. **State vs. transition** — present behavior or non-obvious rationale (keep) vs. relocation / removal / delta-from-old (delete).

**Cheap first-pass filter (flag, don't auto-verdict):** tokens `moved`, `now handled`, `no longer`, `used to`, `previously`, `was`, `replaced`, `instead of`, `per review`, `as requested`, `see <otherfile>` (when explaining an *absence* here). A hit only triggers the cold-reader test — `now` / `instead` also appear in legitimate rationale.

**Sharpest discriminator:** does the comment reference a thing that isn't in this file's current content (a removed block, a moved responsibility, a PR)? Yes → tombstone.

| Comment | Verdict | Why |
|---|---|---|
| "…Release is created by `release.yml`, so this only handles the upload" | delete | Narrates the split; references a removed job. |
| "No checkout needed: `gh` resolves the repo from `GH_REPO`; the guard keeps re-runs idempotent" | keep | Present-state rationale for a non-obvious choice; references only what's in the file. |

## Zombie Code

Code that is dead but still in the tree, or that re-solves an already-solved problem. Every line is a permanent liability someone must read, test, and carry forward — so it must earn its place.

### Reinvention / Not-Invented-Here

**Rule:** Before writing, check whether a well-maintained solution already exists — stdlib, an established library, or an in-repo utility. Reuse it unless a *stated* reason rules it out.

**Discriminator:** Is this a generic, already-solved problem (date math, retries, arg parsing, HTTP, serialization, path handling)? Yes → search first; a hand-rolled version re-shoulders a maintenance burden someone else already carries for you.

Reuse isn't free, so weigh it honestly:

| Prefer reuse when | Consider building when |
|---|---|
| A maintained, widely-used solution fits | Nothing fits, or the dep is unmaintained/abandoned |
| The problem is generic and well-understood | The need is genuinely novel to your domain |
| Reuse cost < build **plus forever-maintain** cost | A heavy dependency for a trivial need (justify it) |

### Dead / Commented-Out Code

**Rule:** Delete dead, unreachable, and commented-out code. Git holds the history — recover it with `git log -G` if ever needed. Never comment code out to keep it "for later"; version control is the "for later."

**Discriminator:** Unreachable (after `return` / `throw` / `break`), unused (no live caller, import, or reference), or disabled/commented "just in case" → delete.

### Orphaned Abstractions / Speculative Generality

**Rule:** Don't build for a future that hasn't arrived (YAGNI). A helper, wrapper, config knob, interface, or parameter with no live consumer is dead weight — remove it, or don't add it.

**Discriminator:** Zero live callers, or added only for a hypothetical future need? → delete / don't write. Generalize when the *second* real use appears, not before.

### Bloat

**Rule:** Surface area must earn its place. Duplicated logic, redundant paths, and unused features inflate what everyone must read, test, and maintain without paying it back.

**Discriminator:** Would removing it lose any current behavior or clarity? No → it's bloat. Collapse real duplication into one owner; extract only when the duplication exists, not when you imagine it might.

**Reuse-vs-reinvent / keep-vs-delete at a glance:**

| Situation | Verdict | Why |
|---|---|---|
| A maintained library already solves this well | reuse | Reinventing is a permanent maintenance cost. |
| Block is unreachable or has no live caller | delete | Dead code; git preserves it. |
| Code commented out "in case we need it" | delete | Version control is the "in case," not the file. |
| Abstraction/param added for a hypothetical future | delete | Speculative generality — add it when a real use lands. |
| Genuinely novel, domain-specific need | build | No existing solution fits; build it and own it. |
