# Praxis

Complete development workflow -- from issue to shipped PR. Includes issue planning, implementation, PR creation, multi-agent code review, and project conventions.

## Installation

Claude Code:

```text
/plugin marketplace add Jartan-LLC/grimoire
/plugin install praxis
```

Codex:

```bash
codex plugin marketplace add Jartan-LLC/grimoire
codex plugin add praxis@grimoire
```

Praxis requires the `gitwise` plugin for commit format, branch naming, and PR
conventions, and declares it as a dependency -- Claude Code installs `gitwise`
automatically. To install it explicitly, run `/plugin install gitwise`.

Codex does not read plugin dependencies, so install it there yourself:

```bash
codex plugin add gitwise@grimoire
```

## What's Included

### Commands

- `/praxis:plan-issue` -- analyze a GitHub issue and create an implementation plan
- `/praxis:implement-issue` -- implement a GitHub issue, optionally from an existing plan
- `/praxis:create-issue` -- create a GitHub issue using the appropriate template
- `/praxis:create-pr` -- create a pull request for implemented changes
- `/praxis:review-pr` -- review a pull request using specialized reviewer agents
- `/praxis:address-review` -- work through review findings on a PR one at a time

### Agents

- **issue-planner** (opus) -- analyzes issues and designs implementation approaches
- **backend-reviewer** -- reviews backend code for patterns, async correctness, security
- **frontend-reviewer** -- reviews frontend code for design system compliance, accessibility
- **general-reviewer** -- reviews code for general quality, naming, organization
- **structure-reviewer** -- reviews structure and readability: decomposition, coupling, interfaces, data modeling, control flow, naming
- **test-reviewer** -- reviews test coverage and CI/CD correctness
- **doc-reviewer** -- reviews documentation for conciseness, accuracy, consistency

### Skills

- **api-error-patterns** -- error response format, status codes
- **code-hygiene** -- zombie code (dead/reinvented/orphaned), tombstone comments
- **code-structure** -- structural craft: decompose on responsibility not size, deep modules, cohesion/coupling/interface/error-contract/data shape
- **docs-patterns** -- writing style, structure, brevity
- **frontend-patterns** -- design tokens, mobile-first, component isolation
- **logging-patterns** -- log levels, formatting, structured output
- **readable-code** -- local clarity: control-flow shape, naming for the reader, reading order and working set
- **review-severity** -- Critical/Important/Minor by consequence-if-shipped
- **testing-patterns** -- integration tests, fixture composition, canary markers

### Hooks

- **UserPromptSubmit** -- prompts the model to load the skills relevant to the
  task. Left alone the model loads a relevant skill only rarely and
  unpredictably, and a skill's own frontmatter does not reliably change that; an
  agent's `skills:` array does, but only inside that agent. The hook names no
  skill and ships no mapping -- the model judges relevance when it holds the
  task. This is what makes every plugin's skills dependably reachable from
  top-level chat, praxis's included.
- **SessionStart** -- installs this plugin's Codex agent roles (no-op outside
  Codex); re-arms skill activation after a compact, which evicts loaded skills
- **PreToolUse** -- reminds you to review changes before `git push`; warns about
  non-standard documentation files; suggests `/compact` at logical intervals
- **PostToolUse** -- checks changed files for stray `console.log`

The compact suggester reports absolute context size and does not know the
model's context window -- a hook cannot determine it -- so on a large-window
session you may want a higher `COMPACT_CONTEXT_THRESHOLD`.

| Setting | Default | Description |
|---|---|---|
| `COMPACT_THRESHOLD` | 50 | tool calls before the first suggestion, then every 25 |
| `COMPACT_CONTEXT_THRESHOLD` | 160000 | context size that triggers a suggestion; `0` disables |
| `COMPACT_CONTEXT_INTERVAL` | 60000 | token growth before the suggestion repeats |

## Workflow

```text
/praxis:plan-issue 42          -> analyze and plan
/praxis:implement-issue 42     -> implement the plan
/praxis:create-pr 42           -> open a pull request
/praxis:review-pr 43           -> multi-agent code review
/praxis:address-review 43      -> work through findings
```

## License

MIT
