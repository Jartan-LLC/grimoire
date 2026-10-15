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

Determine the issue number from the user's request and fetch details:

```bash
gh issue view <issue-number>
```

### 3. Review All Changes

Determine the correct base branch -- `main` for regular branches, or the parent feature branch for sub-issue branches. Read `git diff <base>...HEAD`, the branch's commit messages (`git log <base>..HEAD`), the issue and its plan comment (`gh issue view <issue-number> --comments`), and what this session changed outside the diff (settings, tags, secrets) or did not run. From them, find what the diff alone would let a reviewer miss; ask the user about changes outside the diff that this session did not make. Do not list what was added, modified, and removed.

### 4. Create Pull Request

Learn how the project merges, as `merge-setting.md` in `gitwise:github-conventions` describes: the merge setting decides which text becomes the squash commit's message.

**Title.** Write the PR title as a commit subject: GitHub uses it as the squash commit's subject for a PR with two or more commits under the default setting, and for every PR under the "Pull request title ..." settings. Name the one change and its component in the project's commit format (`<type>(<scope>): <description>` under Conventional Commits). Mark a breaking change as the Commits section of `gitwise:github-conventions` says; a one-time action only contributors owe takes no breaking mark and is flagged in the PR description.

**Description.** Read `.github/PULL_REQUEST_TEMPLATE.md` if the project has one, then write for the merge setting:

- Where the PR description does not become the squash commit's message (GitHub's default), it is the reviewer's briefing: a merge dependency first, as a fact ("Requires #52."), if there is one; what the change is for, in a sentence or two; what the diff alone would let a reviewer miss; how the change was verified; anything the merger or contributors must do. The reasons stay in the commit messages: do not retell them or the diff. Under "Pull request title", add the reasons to the PR description too.
- Where the PR description becomes the squash commit's message, write it as that commit message: start from `git log <base>..HEAD` and the final diff (for a single-commit PR, from that commit's message); give the reasons, and write the intent, flags and verification as facts; each paragraph on one unwrapped line; no template comments or placeholder. Post reviewer notes in a PR comment after creating the PR.
- Where the merge setting is unknown and nobody can be asked, follow the default in `merge-setting.md` in `gitwise:github-conventions`.

```bash
gh pr create --title "<title>" --body "<description>" --base <base-branch>
```

Include `Closes #<issue-number>` in the body.

### 5. Post Update

```bash
gh issue comment <issue-number> --body "Pull request created: <PR-link>"
```
