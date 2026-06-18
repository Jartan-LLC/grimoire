---
description: Build a project using recursive multi-agent development with TDD
argument-hint: Project description, issue number, or plan file path
---

# Recursive Implement

Build a project (or feature) using waves of parallel nested subagents with TDD at every level.

## Process

### 1. Gather Context

Collect everything the orchestrator needs into a single prompt:

- **From `$ARGUMENTS`:** the project description, issue number, or plan file path
- **If issue number:** fetch the issue body with `gh issue view <number>` and include it
- **From conversation:** if the user discussed requirements, architecture decisions, constraints, or preferences in this session, summarize the relevant parts
- **From existing project:** if working in an existing codebase, note the language, test framework, key conventions, and any relevant file paths

### 2. Launch Orchestrator

Spawn a `recursive-orchestrator`. The prompt should contain:

```
[Project description or plan file path]

[Conversation context if any — requirements, constraints, decisions made]

[Existing project context if any — language, conventions, key files]

Working directory: [cwd]
```

### 3. Report Results

Relay the orchestrator's final report to the user.

## Failure Recovery

If the orchestrator reports a failure, present the context to the user. On re-run:
- The wave plan persists in `.claude/workspace/` — pass the file path to skip re-planning
- Completed source files and tests remain on disk — the orchestrator can build on them
