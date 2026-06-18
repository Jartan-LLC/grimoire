---
name: recursive-planning
description: How to decompose projects into wave plans — module identification, dependency mapping, wave assignment, contract guidance, deliverables.
---

# Recursive Planning

## Decomposition Process

1. **Survey** — greenfield or existing? For existing: read README, types, error classes, test setup, conventions. These are constraints.
2. **Identify domains** — genuinely different kinds of work (parsing vs querying vs aggregating vs formatting)
3. **Map dependencies** — which domains need outputs from others? Dependencies flow through interfaces only.
4. **Assign waves** — no dependencies → Wave 1. Depends on Wave 1 → Wave 2. Wave 0 is always contracts/setup. Integration is final wave.
5. **Assign scopes** — each module gets a directory or file set. Zero overlap between parallel modules.
6. **Specify conventions** — language, test framework, type system, DI pattern, path handling, package manager
7. **Plan deliverables** — README, CHANGELOG, `--version`, runtime version access, coverage config

## Module Split Criteria

See `recursive-development` skill for split principle and examples. Goal: natural, best-practice file structure.

## Contract Guidance

Wave 0 agent designs contracts. The plan specifies what they should cover:

- **Enumerate capabilities** — list all operations/formats/modes, not just common ones
- **Error handling** — "Parsers yield Record | ParseError" not "Parsers raise on bad input"
- **Batch interfaces** — "Aggregator takes list[AggregationSpec]" not single-item
- **Injectable I/O** — "Formatters accept a write callable"
- **Types only** — contracts file has protocols, dataclasses, enums, type aliases, constants. No callable stubs.
- **Exception hierarchy** — base exception + subtypes per failure domain
- **Logging** — modules use named loggers, CLI configures at entry point

For existing projects: extend existing contracts, match established patterns.

## Wave Plan Format

Save to `.claude/workspace/wave-plan-<project-name>.md`.

```
## Implementation Plan — `<name>` <description>
### Issue Summary
### Language & Conventions
### Language-Specific Standards
(Standards shaped to this project's language and domain — specifics that all agents must follow.
These go beyond generic conventions. Think about what a senior developer in this language would
insist on in a code review.)
### Existing Patterns (existing projects only)
### Chosen Approach

## Wave 0: Contracts & Project Setup
## Wave 1: <name> (N parallel)
### Module A — Owns: <scope>, Responsibility: <one line>
## Wave 2: <name>
### Module C — Owns: <scope>, Depends on: <interfaces>, Responsibility: <one line>
## Wave N: Integration + Documentation (README.md, CHANGELOG.md)

## File Ownership Map
### Complexity: Simple | Moderate | Complex
```
