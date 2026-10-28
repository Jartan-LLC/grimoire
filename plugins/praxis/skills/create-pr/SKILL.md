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

Load the `gitwise:commit-pr-writing` and `gitwise:github-conventions` skills. Determine the correct base branch, the branch this one was cut from -- `main` for regular branches, the parent feature branch for sub-issue branches, or the lower PR's branch for a branch cut from another open PR's branch (once that PR has merged, the branch rule 2 of `stacks.md` in the `gitwise:github-conventions` skill names). When you cannot tell, ask the user.

When the branch was cut from another PR's branch, other than a sub-issue's parent feature branch, read `stacks.md` before you create the PR, and create it only when its rules say, asking the user when you cannot tell whether the lower PR's review is done; until then, tell the user instead. Once you may create it, and before you read the diff, sync the branch as its rule 2 says, or, when that PR has merged, restack the branch and base the PR as that rule says.

Read `git diff <base>...HEAD` and the branch's commit messages (`git log <base>..HEAD`). Note what this session changed outside the diff (settings, tags, secrets) or did not run, and ask the user about changes outside the diff that this session did not make.

### 4. Create Pull Request

Read `.github/PULL_REQUEST_TEMPLATE.md` if the project has one, and write the PR title and description as `gitwise:commit-pr-writing` says, flagging where the change departs from the plan. When the branch's folder in the workspace has a `pr.md`, start from its title and description and change only what no longer holds against the diff. Then create the PR as a draft, as `gitwise:github-conventions` says:

```bash
gh pr create --draft --title "<title>" --body "<description>" --base <base-branch>
```

Include `Closes #<issue-number>` in the body.

When the base is another open PR's branch, other than a sub-issue's parent feature branch, link the new PR into that PR's stack as `stacks.md` says.
