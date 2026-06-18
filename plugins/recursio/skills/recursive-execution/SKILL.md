---
name: recursive-execution
description: Wave execution rules — agent constraints, wave barriers, review-fix evaluation, language awareness.
when_to_use: Orchestrating or implementing within recursive development waves.
---

# Recursive Execution

## Agent Constraints

These apply to ALL agents in the recursive tree:

- **No worktree isolation.** Never use `isolation: "worktree"`. Worktree agents work in a copy — files get discarded on cleanup.
- **No background agents.** Never use `run_in_background: true`. Background dispatch triggers worktree isolation. Use foreground Agent calls — send parallel agents in a single message for concurrency.
- **Fix delegation.** Simple fixes (unused import, missing return) directly. Logic fixes (bugs, structural merges) via a `recursive-implementer` scoped to affected files with findings in the prompt.
- **Failure escalation.** When a child agent fails: parent retries (max 2), restructures (split differently), or escalates to its own parent. Handle failures at the lowest level that has enough context to fix them.

## Wave Execution

Waves execute sequentially. Within each wave, agents run in parallel.

**Wave barrier:** all agents must complete before running tests or starting the next wave. Send all wave agents as foreground calls in a single message when possible. Sequential dispatch is acceptable when needed.

**Typical structure:**
- Wave 0: Contracts + setup (uses `recursive-implementer`)
- Wave 1+: Implementation modules (parallel `recursive-implementer` agents)
- Final wave: Integration tests + documentation

**Adapting mid-flight:** the orchestrator may add missing deps, adjust types, reorder/merge modules, fix structural issues between waves, and adjust scope boundaries.

## Review-Fix Evaluation

After each wave, spawn a `recursive-reviewer` scoped to the wave's output:

**Post-Wave 0:** review contracts for richness — are interfaces complete enough for downstream modules? Fix gaps directly.

**Post-implementation waves:** review for bugs, structural artifacts, cross-module consistency. Fix Critical findings via implementer agents (max 2 rounds). Note Important findings.

**Post-final wave:** full codebase review. Fix Critical. Verify README.md and CHANGELOG.md exist — create via implementer if missing.

**Report:** total tests, files, max nesting depth, findings summary (found/fixed).

## Language Awareness

The wave plan's **Language & Conventions** section determines:
- Test command (`pytest`, `npx vitest run`, `cargo test`)
- Types/contracts file path
- Setup command (`npm install`, `uv sync`)

Include Language & Conventions in every subagent prompt.
