# Recursio

Recursive multi-agent development system that decomposes projects into waves of parallel nested subagents with TDD at every level. Works for greenfield and existing codebases.

## Installation

Claude Code:

```
/plugin marketplace add Jartan-LLC/grimoire
/plugin install recursio
```

Codex:

```
codex plugin marketplace add Jartan-LLC/grimoire
codex plugin add recursio@grimoire
```

Recursio leans harder on Claude Code than the other plugins. Its skills and
agent roles install under Codex, but nested wave orchestration depends on
spawning subagents that themselves spawn subagents, under per-agent tool
constraints Codex has no equivalent for. Expect `recursive-implement` to behave
differently there.

## What's Included

### Skills

- **recursive-development** -- core principles: nesting, scope ownership, TDD, context flow
- **recursive-planning** -- wave plan design: module identification, dependency mapping, contract guidance
- **recursive-quality** -- quality patterns, anti-patterns, contract richness, critical rules
- **recursive-execution** -- wave barriers, agent constraints, review-fix evaluation

### Agents

- **recursive-orchestrator** (opus) -- coordinates waves of parallel subagents
- **recursive-implementer** (sonnet) -- implements modules with TDD, nests for sub-concerns
- **recursive-planner** (opus) -- architects wave plans from project descriptions
- **recursive-reviewer** (sonnet) -- reviews code for bugs, quality, and structural artifacts

### Commands

- `/recursio:recursive-implement` -- build a project using the full recursive development pipeline

## Quick Start

```
/recursio:recursive-implement Build a CLI tool that parses JSON logs and outputs summary reports
```

## License

MIT
