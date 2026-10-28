---
name: create-pr
description: Create a pull request for implemented changes from a GitHub issue
argument-hint: Issue number (may include additional context)
---

# Create Pull Request

Create a pull request from the current implementation branch for a GitHub issue.

Where the project's own rules say otherwise, follow them.

## Process

### 1. Verify Branch

Check existing local and remote branches for one related to this issue -- it may be named by issue number (`feature/issue-123`) or by description (`feature/audit-improvements`). Check it out and ensure it has committed changes ready for a PR.

### 2. Get Issue Context

Determine the issue number from the user's request and fetch the issue with its comments:

```bash
gh issue view <issue-number> --comments
```

Also load the `praxis:workspace-patterns` skill and read the issue's plan, `.claude/workspace/issue-<issue-number>/plan.md`, or any other plan file in the workspace for this issue.

### 3. Review All Changes

Load the `gitwise:commit-pr-writing` and `gitwise:github-conventions` skills. Determine the correct base branch -- `main` for regular branches, or the parent feature branch for sub-issue branches. Read `git diff <base>...HEAD` and the branch's commit messages (`git log <base>..HEAD`). Note what this session changed outside the diff (settings, tags, secrets) or did not run, and ask the user about changes outside the diff that this session did not make.

### 4. Create Pull Request

If the branch's folder in the workspace has a `pr.md`, take the title and description from it, updating only what no longer holds against the diff. Read `.github/PULL_REQUEST_TEMPLATE.md` if the project has one, and write the PR title and description as `gitwise:commit-pr-writing` says, flagging where the change departs from the plan. Then create the PR as a draft, as `gitwise:github-conventions` says:

```bash
gh pr create --draft --title "<title>" --body "<description>" --base <base-branch>
```

Include `Closes #<issue-number>` in the body.
