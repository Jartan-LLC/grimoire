---
name: implement-issue
description: Implement a GitHub issue, optionally from an existing plan
argument-hint: Issue number (may include additional context)
---

# Implement Issue

Implement changes for a GitHub issue.

Where the project's own rules say otherwise, follow them.

## Process

### 1. Load Context

Determine the issue number from the user's request, which may carry context beyond the number. Fetch the issue and any plan comments:

```bash
gh issue view <issue-number> --comments
```

Also load the `praxis:workspace-patterns` skill and read the issue's plan, `.claude/workspace/issue-<issue-number>/plan.md`, or any other plan file in the workspace for this issue. If no plan exists for a complex issue, suggest running `/praxis:plan-issue` first.

### 2. Setup Branch

Load the `gitwise:github-conventions` skill. Check existing local and remote branches for one related to this issue -- it may be named by issue number (`feature/issue-123`) or by description (`feature/audit-improvements`). If one exists, check it out. If not, create a new branch. For sub-issues of a larger feature, branch from the parent feature branch rather than main. Otherwise, when the issue builds on an open PR's unmerged work, read `stacks.md` in the `gitwise:github-conventions` skill, and branch from that PR's branch when it says to stack.

### 3. Read Relevant Docs

Based on the issue area, read the appropriate project documentation in `docs/`.

### 4. Implement

Load the `gitwise:commit-pr-writing` skill. Before you write code, read `writing.md` in the `praxis:comment-hygiene` skill, even when the skill is already loaded: it covers the comments, docstrings and file headers you write and the ones your change makes false. Follow the plan if one exists. Work through changes methodically. Make progressive commits as logical units of work are completed rather than one monolithic commit at the end, writing each commit message as `gitwise:commit-pr-writing` says.

### 5. Update Documentation

Load the `praxis:docs-patterns` and `praxis:plain-writing` skills. Before you edit any README, CONTRIBUTING.md, release procedure, security policy, docs page, changelog or agent instruction file, read that document's file in `docs-patterns` (`readme.md`, `contributing.md`, `releasing.md`, `security.md`, `docs-pages.md`, `changelog.md`, `agent-files.md`), even when the skill is already loaded. Search every README, docs page and agent instruction file (CLAUDE.md, AGENTS.md, the files they import or name as the rules, `.claude/rules/`, other tools' equivalents) for each command, option, setting, default, path, make target or skill the change adds, renames, removes or alters. Update CONTRIBUTING.md when the change alters setup, the check, a convention or what a change owes. Update the release procedure when the change touches how the project releases (a release workflow, tag pattern, publish job or version rule). Where the project keeps a changelog, add the entry the change owes; where it keeps none, state in the commit message a change consumers see and any step they must take to upgrade. Commit doc changes.

### 6. Verify

Run the Verify commands from the agent instruction files (`CLAUDE.md`, `AGENTS.md` and the files they import). Fix any failures and commit the fixes before pushing.

### 7. Push

Push the branch with all commits. If the branch already has a PR (`gh pr view --json number,title,body,baseRefName`), check its title and description against `git diff <baseRefName>...HEAD`, update what no longer holds as `gitwise:commit-pr-writing` says (`gh pr edit <number>`), and tell the user what you changed.
