# Recursio

Teaches your agent when to split implementation work across parallel subagents, and how to split it so the parts fit together. A change with several parts that are each real work and divide along file or module boundaries is split into small waves, each part built in a fresh context.

A split costs more tokens than building directly.

## Installation

Claude Code:

```text
/plugin marketplace add Jartan-LLC/grimoire
/plugin install recursio
```

Codex:

```bash
codex plugin marketplace add Jartan-LLC/grimoire
codex plugin add recursio@grimoire
```

Recursio leans on Claude Code's subagents. Under Codex the skill and the command load and recursio ships no agent roles. Codex allows one level of subagents by default, so the main thread can split but its parts build their share themselves.

## What's Included

### Skills

- **splitting-implementation** -- whether to split an implementation across parallel subagents, and how: what to settle first, what each subagent is told and reports back, and how each wave is checked on the combined code. The command loads it; otherwise your agent loads it when the work in hand matches its description.

### Commands

- `/recursio:recursive-implement` -- implement a plan file, an issue or a description to completion without stopping to ask, splitting it where that pays. It decides open questions itself and lists each decision in its report. It never commits, branches, pushes, opens a PR or runs a code review: the work is left uncommitted and unreviewed.

## Quick Start

```text
/recursio:recursive-implement Build a CLI tool that parses JSON logs and outputs summary reports
```

To leave Claude Code working until the project's checks pass, use its built-in `/goal` with the project's Verify commands as the condition.

## License

MIT
