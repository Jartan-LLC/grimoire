---
name: review-severity
description: One severity model for code review -- Critical/Important/Minor by consequence-if-shipped (impact x reachability), with confidence as a separate report gate.
when_to_use: Reviewing code, or wiring a reviewer agent -- assigning a tier to a finding, or deciding whether to surface a suspected issue.
---

# Review Severity

Every reviewer tiers findings on one model, so a finding lands the same tier whoever
raises it. A tier is **earned** by a named consequence plus a reachable path -- not by
unease, vividness, or how easy it is to fix.

## The spine

**Severity = consequence-if-shipped = impact x reachability.** Confidence is *not* part
of it (separate gate, below).

- **Impact** = KIND (corruption / breach / crash / wrong-result / disclosure) x MAGNITUDE
  (damage per occurrence) x TIME-HORIZON (irreversibility is just long-horizon impact).
- **Reachability** = P(path reached) x P(trigger), classed **live / edge / dead**. Judge it
  at the **trust boundary** -- a public/exported API or persisted state is a live entry point
  even with no in-repo caller; a *missing or weakened* control on a boundary (authz,
  rate-limit, crypto strength, secure default) defaults **live**, its impact being the breach
  it fails to prevent. And at **intended-completion** for a diff -- a named wiring/flag/call
  path is *pending-live*; only *provably* unwired code is dead. "I couldn't find the caller"
  is not dead.

## Tiers (directives)

- **Critical -- never ship / regenerate.** On a reachable path the code misbehaves or is
  unsafe above the magnitude floor: data loss/corruption (including *silent*), security
  breach, crash/hang/resource-exhaustion, won't build-or-run, broken reference, or a wrong
  result users/callers/downstream act on ("behaves right" means correct *output*, not merely
  "runs"). Also Critical when severe damage is confined to an edge but **irreversible** --
  bounded to three kinds only: (i) silent corruption/loss, (ii) external-contract lock-in
  (published API/schema/event consumers depend on), (iii) irreversible disclosure (secret/
  PII/key that can't be un-leaked). Cost-to-fix never demotes.
- **Important -- avoid; fix by default.** Deferral is a conscious, logged, recoverable choice
  (owner + reason), never silent. Two doors, tagged with a `{landmine | debt}` sub-label:
  **maintainability-debt** -- correct on reachable paths today but a compounding cost a future
  change must pay (missing tests on load-bearing logic, fragile coupling, drift-prone
  duplication, a misleading contract); **recoverable-latent-landmine** -- severe impact whose
  only reachable path is a genuine *recoverable* edge (rare input, flag-gated with a
  named-but-unwired path, an error branch that degrades). Irreversible impact rounds up to
  Critical, never sits here.
- **Minor -- optional polish, safe to leave.** Expected damage ~0 even when reached:
  cosmetic/preference, comments restating code, micro-optimizations with no measured effect,
  debug noise, a non-exploitable info leak. A *severe* defect on **demonstrably-dead** code
  (proven no caller, not exported, no named flag path) is Minor -- latent-flagged so it
  re-tiers the instant a path is wired.

### Magnitude floor (on Critical)
Below the floor, no live path makes a finding Critical. It clears only if a user, caller, or
downstream would make a **materially different decision**, or money/records/persisted-state/
credentials change. A mis-rounded non-critical stat, a wrong tooltip, a non-exploitable info
leak stay low even on a live path. (Security: attacker-reachability alone isn't Critical -- a
generic stack trace or version banner stays low; credential/PII exposure, auth bypass, and
injection clear the floor.)

## Verdict

A review's verdict is its highest tier: **BLOCK** if any Critical, **WARNING** if any
Important but no Critical, **APPROVE** if only Minor or none.

## Boundary tests

- **Critical <-> Important** -- does material-magnitude damage land on a *reachable* path (live,
  attacker-edge, rare-but-guaranteed, or irreversible-on-edge)? -> **Critical**. Correct on
  reachable paths today, or severe damage confined to a *recoverable* edge? -> **Important**.
- **Important <-> Minor** -- is there a named payer of a named accruing cost (drift, untested
  load-bearing logic, a contract that misleads callers), or material impairment of an
  identifiable user class? -> **Important**. Pure taste, no reachable failure, or demonstrably
  dead? -> **Minor**.

## Tie-break

On any boundary, default to the **lower** tier unless you can name the concrete consequence
*and* the reachable path (Critical), or the named payer *and* the accruing cost (Important).
Three counterweights keep default-down from becoming downward drift:

1. **Anti-demotion** -- public/exported API, persisted state, attacker-controlled sinks, and a
   missing control on a boundary default **live**; they can't be waved down by "found no
   caller." Irreversible impact resists demotion.
2. **Anti-aggregation (symmetric)** -- a pile of nits sums to at most one Important, never a
   Critical; a pile of one Important-class defect sums to one systemic Important. Exception
   both ways: repetition that is *one* systemic defect at many sites -> tier the underlying bug.
3. **Magnitude floor** -- as above.

Confidence and cost-to-fix never enter the tie-break.

## Confidence -- a separate report gate

Confidence is never a tier input; a suspected-but-severe finding **keeps** its high tier. The
gate only decides whether to surface it: report if >80% sure; for security, lower the floor to
~50%. **Log-not-drop** suspected criticals (surface as a flagged question) -- don't silently
discard a genuine-but-uncertain severe issue.

The machine-readable record is **two orthogonal fields**: `severity` (an ordered enum) and
`status` (`confirmed` | `suspected`). A CI consumer thresholds *severity* on confirmed
findings (block if >= Critical) and routes suspected to a non-blocking flagged-question
channel. Folding confidence into severity -- or emitting severity with no status field --
collapses the gate and is forbidden.

### Knowledge-cutoff blind spot

A finding that hinges on a post-cutoff fact -- a version you think doesn't exist or is newer
than you know (Sphinx `9.1.0` when you last knew `9.0.0`), a missing API, a deprecation, any
"latest is X" claim -- is a blind spot, never *confirmed* from memory. Presume a
newer-than-known version is real until a live source says otherwise: verify against a registry
(`pip index versions <pkg>`), changelog, or docs before asserting; if you can't, mark it
`suspected`.

## No "Optimization" tier

"Optimize" maps to no directive a generator can act on (block / fix-or-log / polish). Every
optimization item is **Important** (a real accruing cost -- drift-prone duplication, N+1 on a
hot path, a monolith the team churns) or **Minor** (marginal -- cosmetic simplification, a
micro-opt, an O(n^2) loop over a provably-and-enforced tiny bound), chosen by the
Important<->Minor test.

## Extensibility (seams, not machinery)

- Severity is a **named ordinal**; CI thresholds on named levels, not a dense index. A new
  tier appended at an *end* is cheap. A *mid-order* insert -- e.g. splitting Important's
  landmine vs debt into its own tier -- forces a one-time re-tier; it's deferred, and the
  `{landmine|debt}` sub-label pre-shapes that seam. Don't build it before a real dispute.
- A new reviewer category (security / performance / infra) binds to the impact/reachability
  *inputs*, never to new tiers. A "security is always Critical" policy is a post-computation
  `max()` over the enum, not a branch inside the product.
- Per-path / per-project strictness is a post-pass over the pure tier. Precedence: path
  input-overrides (edge->live on a hot path) apply first, then output caps/floors compose via
  max/min. Keep the base computation pure. Hardcode the first override inline; generalize on
  the second.

## Calibration -- illustrative anchors, not a lookup table

Tier a finding by running the spine, not by matching this list. These pin the boundaries:

| Finding | Tier | Reason |
|---|---|---|
| Injection sink on a live path (SQL/XSS) | Critical | breach, live, clears the floor |
| Hardcoded secret in source | Critical | live disclosure; irreversible |
| Inverted validation guard on a live path | Critical | unsafe input admitted |
| Off-by-one that returns wrong/missing records users act on | Critical | wrong output above the floor |
| Broken import (won't run) | Critical | cost-to-fix never demotes |
| Data race / silent-loss on a live path (unsync shared state, un-awaited side effect) | Critical | silent corruption, irreversible |
| Stub / canned return trusted as real on a live path | Critical | wrong output callers act on |
| `except: pass` around a write the caller relies on | Critical | silent loss (Important if the write is recoverable) |
| Blanket `# type: ignore` / suppression | Important | masking debt; any bug it hides tiers on its own |
| Wrong-layer / misleading name / drift-prone duplication | Important | debt a future change pays (floor -- a skipped invariant tiers separately) |
| Missing test on load-bearing logic | Important | named accruing cost |
| Missing alt text on a content image | Important | impairs an identifiable user class |
| Debug `print` left behind | Minor | noise below the floor (Critical if it emits secrets) |
| Dead / commented-out code | Minor | zero behavioral consequence; git owns it |
| Non-conventional casing, comment restating code, unanchored TODO on an incomplete branch | Minor | preference / expected context |
| O(n^2) over a provably-bounded tiny list | Minor | reachability high, impact ~0 |
