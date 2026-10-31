# Recursio

Teaches your agent when to split implementation work across parallel subagents, and how to split it so the parts fit together. A change with several parts that are each real work and divide along file or module boundaries is split into small waves, each part built in a fresh context.

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

## What's Included

### Skills

- **splitting-implementation** -- whether to split an implementation across parallel subagents, and how: what to settle first, what each subagent is told and reports back, and how each wave is checked on the combined code.

## Quick Start

```text
/recursio:splitting-implementation Build a CLI tool that parses JSON logs and outputs summary reports
```

## License

MIT
