# Praxis

Complete development workflow — from issue to shipped PR. Includes issue planning, implementation, PR creation, multi-agent code review, and project conventions.

## Installation

```
/plugin marketplace add Jartan-LLC/grimoire
/plugin install praxis
/plugin install gitwise
```

Praxis requires the `gitwise` plugin for commit format, branch naming, and PR conventions.

## What's Included

### Commands

- `/plan-issue` — analyze a GitHub issue and create an implementation plan
- `/implement-issue` — implement a GitHub issue, optionally from an existing plan
- `/create-issue` — create a GitHub issue using the appropriate template
- `/create-pr` — create a pull request for implemented changes
- `/review-pr` — review a pull request using specialized reviewer agents
- `/address-review` — work through review findings on a PR one at a time

### Agents

- **issue-planner** (opus) — analyzes issues and designs implementation approaches
- **backend-reviewer** — reviews backend code for patterns, async correctness, security
- **frontend-reviewer** — reviews frontend code for design system compliance, accessibility
- **general-reviewer** — reviews code for general quality, naming, organization
- **test-reviewer** — reviews test coverage and CI/CD correctness
- **doc-reviewer** — reviews documentation for conciseness, accuracy, consistency

### Skills

- **api-error-patterns** — error response format, status codes
- **docs-patterns** — writing style, structure, brevity
- **frontend-patterns** — design tokens, mobile-first, component isolation
- **logging-patterns** — log levels, formatting, structured output
- **testing-patterns** — integration tests, fixture composition, canary markers

## Workflow

```
/plan-issue 42          → analyze and plan
/implement-issue 42     → implement the plan
/create-pr 42           → open a pull request
/review-pr 43           → multi-agent code review
/address-review 43      → work through findings
```

## License

MIT
