# Implementation Plan Format

Recommended structure for implementation plans saved in `.claude/workspace/`.

## Template

```markdown
## Implementation Plan

### Issue Summary
Brief restatement of what needs to be done.

### Patterns & Conventions Found
- Pattern: `file:line` -- How the project does similar things

### Chosen Approach
- **What**: Specific approach
- **Why**: Rationale, trade-offs acknowledged
- **How**: High-level steps

### Alternatives Considered
1. Alternative -- why not chosen

### Files to Create/Modify
- `path/file` -- Specific changes

### Documentation Plan
- Which docs need creating or updating

### Implementation Checklist
- [ ] Phase 1: Foundation
- [ ] Phase 2: Core implementation
- [ ] Phase 3: Integration/cleanup

### Complexity
Simple | Moderate | Complex
```

## Guidelines

- Be specific and actionable -- file paths, function names, concrete steps
- Always include alternatives considered, even if briefly
- The documentation plan ensures docs stay current with code
- Phases should be independently verifiable where possible
- If the plan is also posted on GitHub, leave Patterns & Conventions Found, Files to Create/Modify and the Implementation Checklist, which are working notes, out of the posted copy, and never write a bare `#N` in it -- GitHub auto-links it to that issue/PR; use `1.` or `Finding 1` (see the numbering rule at the top of [SKILL.md](SKILL.md))
