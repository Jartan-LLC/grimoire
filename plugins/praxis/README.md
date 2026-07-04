# Praxis

Complete development workflow -- from issue to shipped PR. Includes issue planning, implementation, PR creation, multi-agent code review, and project conventions.

## Installation

```
/plugin marketplace add Jartan-LLC/grimoire
/plugin install praxis
```

Praxis requires the `gitwise` plugin for commit format, branch naming, and PR
conventions, and declares it as a dependency -- Claude Code installs `gitwise`
automatically. To install it explicitly, run `/plugin install gitwise`.

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
- **test-reviewer** -- reviews test coverage and CI/CD correctness
- **doc-reviewer** -- reviews documentation for conciseness, accuracy, consistency

### Skills

- **api-error-patterns** -- error response format, status codes
- **code-hygiene** -- zombie code (dead/reinvented/orphaned), tombstone comments
- **docs-patterns** -- writing style, structure, brevity
- **frontend-patterns** -- design tokens, mobile-first, component isolation
- **logging-patterns** -- log levels, formatting, structured output
- **review-severity** -- Critical/Important/Minor by consequence-if-shipped
- **testing-patterns** -- integration tests, fixture composition, canary markers

## Workflow

```
/praxis:plan-issue 42          -> analyze and plan
/praxis:implement-issue 42     -> implement the plan
/praxis:create-pr 42           -> open a pull request
/praxis:review-pr 43           -> multi-agent code review
/praxis:address-review 43      -> work through findings
```

## License

MIT
