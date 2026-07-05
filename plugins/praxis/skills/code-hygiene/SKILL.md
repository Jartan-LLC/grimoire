---
name: code-hygiene
description: Language-agnostic code hygiene -- honest comments, no dead/reinvented/duplicated code, truthful names, real implementations, and scoped (never blanket) diagnostic suppressions.
when_to_use: Writing or reviewing code -- auditing comments, dead or duplicated code, naming, stubbed/placeholder implementations, or linter/type-checker/test suppressions.
---

# Code Hygiene

Don't leave -- or write -- code that lies, hides, or that git (or an existing solution) already owns. Every line is a permanent liability someone must read, test, and carry forward, so each must earn its place. This skill is language-agnostic and guides both authors and reviewers. This skill only deletes; its constructive siblings shape what survives -- `code-structure` (the units and their contracts) and `readable-code` (how a body reads). (Python-specific pitfalls live in `pythonica:python-anti-patterns`; documentation prose in `docs-patterns`.)

## Comments

A comment earns its place only by telling the reader something the **code cannot**. Sharp test: *could a competent reader recover this fact from the code (and the repo)? Yes -> delete; No -> maybe keep.* One fact survives that test despite being recoverable -- the sole exception, so bake it into the test: a **legal/provenance header** is recoverable from `LICENSE` yet kept inline by mandate (see EXEMPT). The **external-anchor WHY** looks like a second exception but isn't one: naming a constant recovers its *value*, never the spec/constraint that dictated it, so that rationale stays genuinely unrecoverable and keeps on the mainline (see KEEP).

This truthfulness standard applies wherever the annotation lives -- inline comment, block comment, or docstring/doc-comment prose. A doc-comment that restates the signature, lies about behavior, or narrates a change is the same anti-pattern as an inline one. Docstring *format/completeness* defers to the language plugin (`pythonica`); *prose quality* to `docs-patterns`.

### KEEP -- the code can't say it

Phrase each against the **invariant** that motivates it, not the current mechanics, so a refactor leaves it true.

- **WHY / rationale** -- the constraint that forced a non-obvious choice, the tradeoff, or the obvious alternative rejected and why (a performance hack that replaces the clean form belongs here -- say so and cite the evidence: hot path, measured Nx).
  `# gh resolves the repo from GH_REPO, so no checkout; the guard keeps re-runs idempotent`
- **GOTCHA / footgun** -- name the surprising fact, *then* why it must be so: a side effect a caller can't infer (a read that writes, a getter that primes a cache, hidden I/O or global mutation), an ordering dependency (say what silently breaks if reordered), a looks-wrong-but-right oddity (a correct off-by-one, a deliberate bare except), a cost/thread hazard, or a decode of genuinely inscrutable syntax. A warning without its why is just a WHAT-comment with an alarm on it. Delete it the moment the hazard is removed, or it becomes a phantom warning.
  `# <= not <: the upper bound is inclusive per the wire spec`
- **EXTERNAL ANCHOR** -- a citation to the spec/RFC/ticket/paper/formula/legal requirement that dictates the code's shape. The most rot-resistant comment there is: its source of truth is versioned and changes deliberately elsewhere. Distinguish from Nonlocal (DELETE): citing a *versioned* spec/RFC/ticket anchors (keep); mirroring a value a *live, mutable* config or another service owns only drifts (delete).
  `# 0x5F3759DF: fast inverse-sqrt magic constant, see Quake III src`

### EXEMPT -- functional, not prose

Judged by *"is it required?"*, not *"does it convey rationale?"* -- the prose taxonomy has no slot for annotations that use comment syntax but are machine-read. A reviewer applying "banner/noise -> delete" literally will break tooling.

- **Legal / provenance header** -- license, copyright, SPDX mandated by law or policy. Keep minimal; point to `LICENSE` rather than inlining the full text. `# SPDX-License-Identifier: Apache-2.0`. Restrict "provenance" to legal/origin -- **not** author credit (`# Author: Jane` is a byline -> delete). Mandated *per-line* boilerplate -> delete; mandated *per-file legal* header -> keep.
- **Tooling directive** -- load-bearing to a machine, not a reader: shebang, encoding cookie, `# %%` cell marker, `# region`/`#endregion` fold, `# fmt: off`, codegen sentinel (`# BEGIN GENERATED`), type-in-comment hint, and scoped suppression pragmas (`# noqa`, `# type: ignore` -- scoping governed in *Faking done*). Not a decorative banner (below).

### DELETE -- recoverable, or git owns it

Cover the comment, read only the code; if a competent reader learns nothing new, delete it.

- **What / how restatement** -- paraphrases the mechanics the line states (`i += 1  # increment i`). Highest-coupling, fastest-rotting comment: a lie the instant the mechanics change and no one updates it.
- **Derived-value echo** -- restates a value, count, threshold, or range the code already declares. No compiler catches the drift -> delete *even when currently correct*, on rot risk alone.
- **Stale / misleading** -- the current code contradicts it. Worse than none: correct it into a keep-category fact, or delete.
- **Nonlocal** -- asserts a fact another file/service/config owns; it drifts silently when *that* source changes. State it at the source. (Cross-ownership drift, distinct from mere in-repo duplication.)
- **Noise / banner / attribution** -- section dividers (`# ==== HELPERS ====`), closing-brace labels (`} // end for`), author/date bylines. Structure and `git blame` carry these; if a file needs dividers to navigate, split it. (A `# region` fold or codegen sentinel is a tooling directive, not a banner.)
- **Commented-out code** -- delete unconditionally; git owns it (`git log -G` recovers it). "Disabled with a why" is no loophole -- the code still goes, only the codeless knowledge survives as a tracked note. See *Dead code*. Carve-out: an illustrative snippet inside a docstring/example config is documentation-by-example, not disabled program code -> keep.
- **Mandated boilerplate** -- a comment satisfying only a "comment everything" rule, or a header restating the signature's name/params/return. If a header is required, make it say what the signature cannot.

#### Tombstone -- narrates the change, not the state

Narrates the **change** that produced the code (what was removed, moved, renamed, or done "per review") rather than its current state. Git owns change history; such comments duplicate the diff, drift, and mean nothing to a reader who never saw the prior version. Two tests, in order:
1. **Cold-reader** -- worth writing to a first-time reader who never saw the prior version or the PR? No -> delete.
2. **Git-ownership** -- amounts to "what changed/moved/was removed", or points to a thing not in this file now (a removed block, a moved responsibility, a PR)? Version control's job -> delete.

**First-pass token filter (flag, don't auto-verdict):** `moved`, `now handled`, `no longer`, `used to`, `previously`, `was`, `replaced`, `instead of`, `per review`, `as requested`, `see <otherfile>` (explaining an *absence* here). A hit only triggers the cold-reader test -- `now`/`instead` also appear in legitimate rationale.

### CONDITIONAL

- **TODO / FIXME / HACK** -- KEEP only if actionable *and* anchored to a tracker: `TODO(#123): drop once upstream ships stubs` states what the code can't (known-incomplete, and what's owed) -> treat as an external anchor. Flag the bare orphan (`TODO: fix later`) -- no owner, rots. Never delete a *live, real-gap* marker for cleanliness; that hides debt, which is worse.
- **Magic value** -- SPLIT. The value's **meaning** -> self-document with a named constant (meta-rule) and drop the comment. Its **provenance** (spec section, RFC, empirically-tuned figure, bit-hack origin) -> KEEP as external-anchor WHY. A bare number with neither name nor anchor is a naming defect, not a comment to keep.

### Keep vs. delete

| Comment | Verdict | Why |
|---|---|---|
| `# gh resolves the repo from GH_REPO; the guard keeps re-runs idempotent` | keep | WHY -- present-state rationale for a non-obvious choice. |
| `# SPDX-License-Identifier: Apache-2.0` | keep | Legal header -- mandated; `git blame` can't carry it. |
| `# TODO(#123): remove once upstream ships stubs` | keep | Tracked gap -- an anchor to versioned debt. |
| `i += 1  # increment i` | delete | What restatement -- restates the line verbatim. |
| `# retries 3 times` beside a loop of 5 | delete | Stale/derived -- updating the count just re-creates the echo; elevate to a WHY instead. |
| `# timeout is 30s`, value lives in another service's config | delete | Nonlocal -- drifts when that config changes; state it at the source. |
| "...Release is created by `release.yml`, so this only handles upload" | delete | Tombstone -- narrates the split; references a removed job. |
| `# Author: Jane` * `# ==== HELPERS ====` * `} // end for` | delete | Byline / banner -- `git blame` and structure own these. |
| `x = f()  # TODO: fix later` | flag | Orphan TODO -- no owner, no anchor; anchor it or resolve it. |

### Meta-rule

Prefer self-documenting code over a comment. A better name or an extracted function is **load-bearing** -- a refactor carries it along, so it can't drift out of sync the way a bystander comment silently does. If a rename or extraction would carry the fact, do that instead. Reach for a comment only for the residue the code genuinely can't hold: a WHY, a gotcha, an external anchor.

## Dead code & speculative generality

Code no live path needs is dead -- delete it; don't add what isn't needed yet.

### Dead / commented-out code

**Rule:** Delete dead, unreachable, and commented-out code. Git holds the history -- recover it with `git log -G` if ever needed. Never comment code out to keep it "for later"; version control *is* the "for later."

**Test:** unreachable (after `return` / `throw` / `break`), unused (no live caller, import, or reference), or disabled/commented "just in case" -> delete.

### Orphaned abstractions / speculative generality

**Rule:** Don't build for a future that hasn't arrived (YAGNI). A helper, wrapper, config knob, interface, or parameter with no live consumer is dead weight -- remove it, or don't add it.

**Test:** zero live callers, or added only for a hypothetical future need? -> delete / don't write. Generalize when the *second* real use appears, not before.

### Debug / scaffolding output left behind

**Rule:** Strip ad-hoc debug and instrumentation output -- `print`, `console.log`, `debugger`, `breakpoint()`, `dbg!`, `var_dump` -- before merge. It was scaffolding to inspect state during development, not shipped behavior.

**Test:** is this line an ad-hoc trace a developer added to watch state, rather than an intentional logger call? Yes -> delete.

**Contrast:** a real logger call (`logger.*`) is the sanctioned channel for output that *should* ship -- see `logging-patterns`.

## Reinvention & duplication

### Reinvention / Not-Invented-Here

**Rule:** Before writing, check whether a well-maintained solution already exists -- stdlib, an established library, or an in-repo utility. Reuse it unless a *stated* reason rules it out.

**Test:** is this a generic, already-solved problem (date math, retries, arg parsing, HTTP, serialization, path handling)? Yes -> search first; a hand-rolled version re-shoulders a maintenance burden someone else already carries for you.

Reuse isn't free, so weigh it honestly:

| Prefer reuse when | Consider building when |
|---|---|
| A maintained, widely-used solution fits | Nothing fits, or the dep is unmaintained/abandoned |
| The problem is generic and well-understood | The need is genuinely novel to your domain |
| Reuse cost < build **plus forever-maintain** cost | A heavy dependency for a trivial need (justify it) |

### Bloat / duplication

**Rule:** Duplication multiplies every future edit site -- one change must then be made in many places, and one gets missed. Collapse repeated logic into a single owner.

**Test:** does the same logic appear in more than one place? Fold it into one owner -- but extract on the *second* real use, not an imagined one.

## Naming

### Misleading name -- a name that lies

**Rule:** An identifier, file, or flag must tell the truth about what it is or does -- rename anything whose name contradicts its behavior, scope, or type.

**Test:** does the name promise something the code doesn't deliver -- a `get_*`/`is_*` that mutates, a boolean flag whose name is the inverse of its effect, a count that holds a list, a `utils`/`helpers` grab-bag that owns real domain logic?

| Name | Verdict | Why |
|---|---|---|
| `get_user()` that also writes a login timestamp | rename | `get_*` promises a pure read; make it `fetch_and_touch_user`, or split the write out. |
| `disable_cache=False` that actually *enables* verbose logging | rename | Flag name is the inverse of -- and unrelated to -- its effect. |
| `user_count` bound to a list of users | rename | Type/name mismatch; it's `users`. |

### Non-descriptive name -- a name that says nothing

**Rule:** An identifier must state what it holds or does. Rename placeholder and grab-bag names shipped in committed code -- `foo`, `tmp`, `data`, `obj`, `thing`, `do_stuff`, and vague `*Manager` / `*Handler` catch-alls.

**Test:** can a reader state what the identifier holds or does from the name alone? No -> rename. (Distinct from a misleading name: that one lies; this one is merely empty.)

## Faking done: stubs & silenced checks

Don't ship work that only looks finished -- a stub on a live path, or a red check clubbed green. Both hide unfinished or broken code from the next reader and from the toolchain.

### Placeholder implementation masquerading as complete

**Rule:** Reachable code on a real path must actually do its job; don't ship a stub, silent no-op, or hardcoded/fake return that only looks finished.

**Test:** does a function with live callers return a canned/constant value, a no-op (`pass`), or `raise NotImplementedError` while presenting as done -- with no honest, tracked TODO flagging it as unfinished?

**Contrast:** an explicit `NotImplementedError` or a tracked TODO the caller expects -> honest and fine. A silent fake that callers trust as real -> not.

### Blanket suppression directive (silenced diagnostic)

**Rule:** Never silence a linter, type-checker, compiler, or test to go green. Fix the cause; if you genuinely must suppress, scope it to the single line and the single rule, and state the reason inline.

**Test:** is there a suppression directive -- `# noqa`, `# type: ignore`, `eslint-disable` / `@ts-ignore` / `@ts-nocheck`, `@SuppressWarnings`, `#pragma warning disable`, `//nolint` -- that is bare (no reason) or broader than the one line/rule it excuses (file-level or blanket)?

| Directive | Verdict | Why |
|---|---|---|
| `# type: ignore` at file top | fix | Blanket -- silences every type error in the file. |
| `x = untyped()  # type: ignore[no-any-return]  # lib ships no stubs; tracked in #123` | keep | Scoped to one line and one rule, with a reason. |
| `// eslint-disable-next-line no-eval -- sandboxed input, see SECURITY.md` | keep | One line, one rule, justified. |
