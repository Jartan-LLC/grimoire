# Memoria

Session memory and continuous learning for Claude Code. Preserves context across sessions, extracts patterns from your work, and evolves atomic instincts into reusable skills.

## Installation

```
/plugin marketplace add Jartan-LLC/grimoire
/plugin install memoria
```

## What's Included

### Session Memory

Cross-session context that survives between conversations:
- **Session start** — loads previous session summary, learned skills, and aliases
- **Session end** — persists current session state (tasks, files modified, tools used)
- **Compaction** — saves state before context compression, suggests strategic compaction points

### Continuous Learning (v2)

Instinct-based learning system that observes your work and extracts patterns:
- **Observation hooks** — capture every tool call (PreToolUse/PostToolUse)
- **Observer agent** — background Haiku agent analyzes observations, creates atomic instincts
- **Confidence scoring** — instincts score 0.3-0.9, grow with confirmation, decay without use
- **Evolution** — instincts cluster into skills, commands, or agents over time

### Commands

- `/sessions` — list, load, alias, and manage session history
- `/instinct-status` — show learned instincts with confidence levels
- `/instinct-export` — export instincts for sharing
- `/instinct-import` — import instincts from others
- `/evolve` — cluster instincts into skills, commands, or agents
- `/learn-eval` — extract patterns from current session
- `/learn` — manually teach a pattern

## How It Works

```
Session → Observation Hooks → observations.jsonl
                                    ↓
                            Observer Agent (Haiku)
                                    ↓
                        Atomic Instincts (0.3-0.9 confidence)
                                    ↓
                        /evolve → Skills / Commands / Agents
```

Instincts are stored in `~/.claude/homunculus/instincts/`. Each is a single trigger-action pair with evidence tracking and confidence scoring.

## Credits

Session management and continuous learning system adapted from [everything-claude-code](https://github.com/affaan-m/everything-claude-code) by Affaan Mustafa.

## License

MIT
