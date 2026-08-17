---
name: comment-hygiene
description: Comment truthfulness -- what a comment must tell the reader that the code can't, the KEEP/DELETE/EXEMPT/CONDITIONAL taxonomy, tombstone and retold-fact detection, and comment density across a diff. Sibling to code-hygiene, code-structure and readable-code.
when_to_use: Writing or reviewing code -- auditing whether a comment, docstring, or doc-comment earns its place, spotting stale/tombstone/retold comments, or judging comment density across a diff.
user-invocable: false
---

# Comment Hygiene

Split from `code-hygiene` -- this is comment truthfulness only; dead code, reinvention/duplication, naming, and faking done stay in `code-hygiene`, which this skill sits alongside as a sibling of `code-structure` (the units and their contracts) and `readable-code` (how a body reads).

A comment earns its place only by telling the reader something the **code cannot**. Sharp test: *could a competent reader recover this fact from the code (and the repo)? Yes -> delete; No -> maybe keep.* One fact survives that test despite being recoverable -- the sole exception, so bake it into the test: a **legal/provenance header** is recoverable from `LICENSE` yet kept inline by mandate (see EXEMPT). The **external-anchor WHY** looks like a second exception but isn't one: naming a constant recovers its *value*, never the spec/constraint that dictated it, so that rationale stays genuinely unrecoverable and keeps on the mainline (see KEEP).

This truthfulness standard applies wherever the annotation lives -- inline comment, block comment, or docstring/doc-comment prose. A doc-comment that restates the signature, lies about behavior, or narrates a change is the same anti-pattern as an inline one. Docstring *format/completeness* defers to the language plugin (`pythonica`); *prose quality* to `docs-patterns`.

## KEEP -- the code can't say it

Phrase each against the **invariant** that motivates it, not the current mechanics -- **evergreen**, so a refactor leaves it true.

- **WHY / rationale** -- the constraint that forced a non-obvious choice, the tradeoff, or the obvious alternative rejected and why (a performance hack that replaces the clean form belongs here -- say so and cite the evidence: hot path, measured Nx).
  `# gh resolves the repo from GH_REPO, so no checkout; the guard keeps re-runs idempotent`
- **GOTCHA / footgun** -- name the surprising fact, *then* why it must be so: a side effect a caller can't infer (a read that writes, a getter that primes a cache, hidden I/O or global mutation), an ordering dependency (say what silently breaks if reordered), a looks-wrong-but-right oddity (a correct off-by-one, a deliberate bare except), a cost/thread hazard, or a decode of genuinely inscrutable syntax. A warning without its why is just a WHAT-comment with an alarm on it. Delete it the moment the hazard is removed, or it becomes a phantom warning.
  `# <= not <: the upper bound is inclusive per the wire spec`
- **EXTERNAL ANCHOR** -- a citation to the spec/RFC/ticket/paper/formula/legal requirement that dictates the code's shape. The most rot-resistant comment there is: its source of truth is versioned and changes deliberately elsewhere. Distinguish from Nonlocal (DELETE): citing a *versioned* spec/RFC/ticket anchors (keep); mirroring a value a *live, mutable* config or another service owns only drifts (delete).
  `# 0x5F3759DF: fast inverse-sqrt magic constant, see Quake III src`

## EXEMPT -- functional, not prose

Judged by *"is it required?"*, not *"does it convey rationale?"* -- the prose taxonomy has no slot for annotations that use comment syntax but are machine-read. A reviewer applying "banner/noise -> delete" literally will break tooling.

- **Legal / provenance header** -- license, copyright, SPDX mandated by law or policy. Keep minimal; point to `LICENSE` rather than inlining the full text. `# SPDX-License-Identifier: Apache-2.0`. Restrict "provenance" to legal/origin -- **not** author credit (`# Author: Jane` is a byline -> delete). Mandated *per-line* boilerplate -> delete; mandated *per-file legal* header -> keep.
- **Tooling directive** -- load-bearing to a machine, not a reader: shebang, encoding cookie, `# %%` cell marker, `# region`/`#endregion` fold, `# fmt: off`, codegen sentinel (`# BEGIN GENERATED`), type-in-comment hint, and scoped suppression pragmas (`# noqa`, `# type: ignore` -- scoping governed in `code-hygiene`'s *Faking done*). Not a decorative banner (below).

## DELETE -- recoverable, or git owns it

Cover the comment, read only the code; if a competent reader learns nothing new, delete it.

- **What / how restatement** -- paraphrases the mechanics the line states (`i += 1  # increment i`). Highest-coupling, fastest-rotting comment: a lie the instant the mechanics change and no one updates it.
- **Derived-value echo** -- restates a value, count, threshold, or range the code already declares. No compiler catches the drift -> delete *even when currently correct*, on rot risk alone.
- **Stale / misleading** -- the current code contradicts it. Worse than none: correct it into a keep-category fact, or delete.
- **Nonlocal** -- asserts a fact another file/service/config owns; it drifts silently when *that* source changes. State it at the source. (Cross-ownership drift: told here, never at its owner -- move it there. If the repo already states it at the owner, that copy is *Retold fact* under CONDITIONAL -- point, don't restate.)
- **Noise / banner / attribution** -- section dividers (`# ==== HELPERS ====`), closing-brace labels (`} // end for`), author/date bylines. Structure and `git blame` carry these; if a file needs dividers to navigate, split it. (A `# region` fold or codegen sentinel is a tooling directive, not a banner.)
- **Commented-out code** -- delete unconditionally; git owns it (`git log -G` recovers it). "Disabled with a why" is no loophole -- the code still goes, only the codeless knowledge survives as a tracked note. See `code-hygiene`'s *Dead code*. Carve-out: an illustrative snippet inside a docstring/example config is documentation-by-example, not disabled program code -> keep.
- **Mandated boilerplate** -- a comment satisfying only a "comment everything" rule, or a header restating the signature's name/params/return. If a header is required, make it say what the signature cannot.

### Tombstone -- narrates the change, not the state

Narrates the **change** that produced the code (what was removed, moved, renamed, or done "per review") rather than its current state. A state description is evergreen; a change narration is dated the moment it is written. Git owns change history; such comments duplicate the diff, drift, and mean nothing to a reader who never saw the prior version. Two tests, in order:

1. **Cold-reader** -- worth writing to a first-time reader who never saw the prior version or the PR? No -> delete.
2. **Git-ownership** -- amounts to "what changed/moved/was removed", or points to a thing not in this file now (a removed block, a moved responsibility, a PR)? Version control's job -> delete.

**First-pass token filter (flag, don't auto-verdict):** `moved`, `now handled`, `no longer`, `used to`, `previously`, `was`, `replaced`, `instead of`, `per review`, `as requested`, `see <otherfile>` (explaining an *absence* here). A hit only triggers the cold-reader test -- `now`/`instead` also appear in legitimate rationale, and a **Dated advisory** legitimately uses `no longer`/`was` about the world outside this repo.

## CONDITIONAL

- **TODO / FIXME / HACK** -- KEEP only if actionable *and* anchored to a tracker: `TODO(#123): drop once upstream ships stubs` states what the code can't (known-incomplete, and what's owed) -> treat as an external anchor. Flag the bare orphan (`TODO: fix later`) -- no owner, rots. Never delete a *live, real-gap* marker for cleanliness; that hides debt, which is worse.
- **Magic value** -- SPLIT. The value's **meaning** -> self-document with a named constant (meta-rule) and drop the comment. Its **provenance** (spec section, RFC, empirically-tuned figure, bit-hack origin) -> KEEP as external-anchor WHY. A bare number with neither name nor anchor is a naming defect, not a comment to keep.
- **Dated advisory** -- the one deliberate exception to evergreen. A fact about the world
  *outside this repo* that you cannot fix from here: an unpatched CVE, an upstream bug you
  compensate for. Undated it turns false the day the world moves, so it needs an **anchor**
  (advisory or tracker id, never a person), an **as-of date**, and the **impact here**.
  Phrase it to name its own end -- "no fixed release as of `<date>`" stops being true once one
  ships, which is when the comment goes. Unlike a TODO, the fix is not ours to make.
  `# CVE-2025-1234 in libfoo <= 2.3, no fixed release as of 2026-08-05; affected parser unreachable here`
- **Retold fact** -- SPLIT. A keep-category fact told again at a second site: every copy is
  true and locally unrecoverable, so per-file review keeps them all and one edit later the
  rest read as lies. The site whose own change would falsify it KEEPs the telling; the others
  name the topic and point (`# config ownership: entrypoint.sh`), though a warning at its own
  point of danger stays. Grep the phrase before ruling, or run
  [find-duplicate-comments.js](find-duplicate-comments.js), which indexes every tracked
  comment and reports the ones a diff adds that are already told elsewhere.

## Keep vs. delete

| Comment | Verdict | Why |
|---|---|---|
| `# gh resolves the repo from GH_REPO; the guard keeps re-runs idempotent` | keep | WHY -- present-state rationale for a non-obvious choice. |
| `# SPDX-License-Identifier: Apache-2.0` | keep | Legal header -- mandated; `git blame` can't carry it. |
| `# TODO(#123): remove once upstream ships stubs` | keep | Tracked gap -- an anchor to versioned debt. |
| `i += 1  # increment i` | delete | What restatement -- restates the line verbatim. |
| `# retries 3 times` beside a loop of 5 | delete | Stale/derived -- updating the count just re-creates the echo; elevate to a WHY instead. |
| `# timeout is 30s`, value lives in another service's config | delete | Nonlocal -- drifts when that config changes; state it at the source. |
| "...Release is created by `release.yml`, so this only handles upload" | delete | Tombstone -- narrates the split; references a removed job. |
| `# Author: Jane` \* `# ==== HELPERS ====` \* `} // end for` | delete | Byline / banner -- `git blame` and structure own these. |
| `x = f()  # TODO: fix later` | flag | Orphan TODO -- no owner, no anchor; anchor it or resolve it. |
| `# CVE-2025-1234 in libfoo <= 2.3, no fixed release as of 2026-08-05; affected parser unreachable here` | keep | Dated advisory -- anchored, dated, scoped; a fix retires it. |
| The same "Geyser owns the config after first boot" in six files | split | Retold fact -- keep it where a change would falsify it; the rest point. |

## Density -- judge the diff, not just the comment

Every rule above weighs one comment against the code beside it, so a diff can pass at every single site and still ship bloat: *"does this fact earn a comment?"* is a different question from *"does this file need this many?"*. Ask the second one once, over the whole diff.

**Trigger** -- a signal to re-read, never a budget to hit: added comment lines approaching or exceeding added code lines, or a rationale on nearly every changed block. Then re-read each one with the presumption reversed, because the first pass was made in the mood that wrote them.

**The usual cause is PR narration** -- the author explains the change to the reviewer, then writes that explanation into the file. Sort by reader: a sentence aimed at whoever reads the **diff** belongs in the PR body, where it is read once by the reader it was written for and never rots; only a sentence aimed at whoever reads the **file** years later stays. The migration story, the measurement that justified the switch, and the comparison to what used to be here are all the first kind (and the last is a Tombstone besides).

**A rejected alternative splits on that same test.** One a future editor would otherwise re-attempt is a WHY and stays inline; one that only explains why *this change* looks the way it does goes in the PR body.

What survives is one invariant per non-obvious decision, at the site whose own change would falsify it -- the sites that share it name the topic and point (*Retold fact*).

## Meta-rule

Prefer self-documenting code over a comment. A better name or an extracted function is **load-bearing** -- a refactor carries it along, so it can't drift out of sync the way a bystander comment silently does. If a rename or extraction would carry the fact, do that instead. Reach for a comment only for the residue the code genuinely can't hold: a WHY, a gotcha, an external anchor.
