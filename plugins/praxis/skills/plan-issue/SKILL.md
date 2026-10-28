---
name: plan-issue
description: Analyze a GitHub issue and create an implementation plan
argument-hint: Issue number (may include additional context)
---

# Plan Issue

Create an implementation plan for a GitHub issue.

## Process

### 1. Load Issue

Determine the issue number from the user's request, which may carry context beyond the number. Fetch the issue details:

```bash
gh issue view <issue-number>
```

### 2. Read Relevant Docs

Based on the issue area, read the appropriate project documentation in `docs/`.

### 3. Explore Codebase

Find existing patterns similar to what the issue requires. Look at how comparable features are already implemented.

### 4. Assess Scope

Evaluate whether the issue should be broken into sub-issues. Not every multi-part feature needs splitting -- but large features degrade in quality when implemented in a single AI context. Consider splitting when:

- **The diff would be very large** -- Thousands of lines in one pass means mistakes get buried. Smaller, focused issues produce better results.
- **There are genuinely separable concerns** -- A reusable module that happens to be needed by this feature is worth its own issue. A small page that accompanies a backend feature is not.

If sub-issues are warranted, use `/praxis:create-issue` to file them, referencing the parent issue. Sub-issue branches are created from the parent feature branch, or from another sub-issue's branch when they stack (`stacks.md` in `gitwise:github-conventions`), and merge back into it, not directly to main.

### 5. Design Considerations

Before creating the plan, think through:

- **Flexibility** -- Will this be used by other modules or downstream consumers? Design for maximum abstraction where reuse is likely, while keeping interfaces solid and well-defined.
- **Robustness** -- Clear models, explicit types, proper error handling. Flexible internals, rigid contracts.
- **Future-proofing** -- Consider how this might need to evolve without requiring breaking changes.
- **Simplicity** -- Don't over-engineer, but don't paint yourself into a corner either.

### 6. Create Plan

Load the `praxis:workspace-patterns` skill. Write the plan to the issue's folder in the workspace, `.claude/workspace/issue-<issue-number>/plan.md`, following the format in the `gitwise:github-conventions` skill (see `plan-format.md`), and tell the user its path.
