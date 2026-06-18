---
name: recursive-development
description: Core principles for recursive multi-agent development — nesting, scope ownership, TDD, context flow, token economics.
when_to_use: Any work involving recursive subagent orchestration.
---

# Recursive Development

Decompose work into waves of parallel nested subagents. Works for greenfield and existing codebases. Each wave completes before the next starts. Within a wave, independent modules run in parallel. No depth limit on nesting.

For existing projects, Wave 0 extends established patterns rather than creating from scratch.

## Nesting

Default to nesting. Each nested agent has smaller context — faster and cheaper per-agent. A flat agent juggling 7 files costs more than 3 focused agents each handling 2-3 files.

Nest when a module contains distinct algorithms or domains. Stop when atomic (single concern, single file). Split by **algorithm or domain**, not by testability alone.

### When to split — examples

The same principle applies at every level of recursion:

**Split** (distinct algorithms or domains):
- Parsers + filters + aggregation + formatters — different domains
- Cycle detection + topological sort — different graph algorithms
- JSONL parser + CLF parser + CSV parser — different parsing algorithms
- Expression parser + predicate evaluator — syntax parsing vs logic evaluation

**Don't split** (steps in one operation, or trivial wrappers):
- File discovery + file reading + format detection — one operation ("load config")
- A parser that just delegates to a validator — no distinct logic
- Output capture separate from execution — capturing is part of executing

| Role | Scope | Spawns when... |
|------|-------|----------------|
| **Orchestrator** | Shared files + wave sequencing | Always |
| **Module agent** | Directory scope | 2+ testable concerns |
| **Component agent** | File set scope | Separable sub-concerns |
| **Leaf agent** | Single file pair | Never — implements directly |

### Model selection

| Level | Recommended model |
|-------|-------------------|
| Orchestrator | **opus** — decomposition, contract design |
| Module/component | **sonnet** — focused, contract-constrained |

## Scope-Based Ownership

**No two parallel subagents may touch the same file.**

| Level | Typical scope |
|-------|--------------|
| Wave | Directory (`src/config/`) |
| Module | Directory or file set |
| Sub-component | File set (`['parser.ts', 'parser.test.ts']`) |

Directory scope: agent creates any files under it. File set scope: agent touches only listed files. Shared files (types, index) owned by parent wave, read-only after.

Before dispatching: assign scopes, verify zero overlap, create shared files first.

## TDD at Every Level

1. Parent defines contracts
2. Agent writes tests first
3. Agent implements to pass
4. Agent verifies (runs tests)

At levels with multiple concerns, delegate steps 2-4 to child agents.

## Context Flow

**Down:** contracts, ownership scope, dependency interfaces.
**Up:** pass/fail, interface change requests, files created.
**Never down:** full plan, other modules' code. **Never up:** internal decisions.

## Token Economics

More agents with less context each > fewer agents with large context. Pass minimal context — contract and ownership only. The orchestrator is the most expensive agent; keep it thin.

## Style Consistency

Spawn `recursive-implementer` for all module agents. Children use the same type. Style contract propagates down the tree. Prompts stay minimal — the agent definition carries the rest.
