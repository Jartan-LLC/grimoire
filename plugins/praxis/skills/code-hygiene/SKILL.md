---
name: code-hygiene
description: Language-agnostic code hygiene -- no dead/reinvented/duplicated code, truthful names, real implementations, and scoped (never blanket) diagnostic suppressions.
when_to_use: Writing or reviewing code -- auditing dead or duplicated code, naming, stubbed/placeholder implementations, or linter/type-checker/test suppressions.
user-invocable: false
---

# Code Hygiene

Don't leave -- or write -- code that lies, hides, or that git (or an existing solution) already owns. Every line is a permanent liability someone must read, test, and carry forward, so each must earn its place. This skill is language-agnostic and guides both authors and reviewers. This skill only deletes; its constructive siblings shape what survives -- `code-structure` (the units and their contracts) and `readable-code` (how a body reads). Comment truthfulness is `comment-hygiene`'s. (Python-specific pitfalls live in `pythonica:python-anti-patterns`; documentation prose in `docs-patterns`.)

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
