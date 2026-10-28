---
name: review-pr
description: Review a pull request, or a branch before it has one, using specialized reviewer agents
argument-hint: PR number or branch (may include additional context)
---

# Review PR

Review a pull request, or a branch before it has one, with category-based reviewer agents.

## Process

### 1. Get the Change

Determine what to review from the user's request, which may carry context beyond it: a PR number or a branch; with neither, the current branch. A branch with a PR (`gh pr view <branch> --json number`) is reviewed as that PR.

For a PR, fetch its details and diff:

```bash
gh pr view <pr-number>
gh pr diff <pr-number>
gh pr view <pr-number> --json title,body,commits,headRefName,isCrossRepository
```

For a branch with no PR, the change is `git diff <base>...<branch>` and its commit messages `git log --format=%B <base>..<branch>`. The base is the one the request names; otherwise the branch it was cut from: the default branch, or for a sub-issue or stacked branch the branch below it. When you cannot tell, ask. Load the `praxis:workspace-patterns` skill: the branch's `pr.md`, when it has one, is its PR title and description.

Reviewers read files from a checkout of the branch: when the branch is local but checked out elsewhere, use that checkout or add a worktree as `praxis:workspace-patterns` says. Never switch another checkout's branch.

### 2. Categorize and Review

Launch relevant reviewer agents based on changed files:

- Backend changes -> `backend-reviewer`
- Frontend changes -> `frontend-reviewer`
- CI/test changes -> `test-reviewer`
- Non-trivial code changes -> `structure-reviewer`
- All changes -> `general-reviewer`
- All changes -> `doc-reviewer`, given the PR title, the PR description and the commit messages

### 3. Verify Documentation

`doc-reviewer` owns doc-code mismatch: where code changed public behavior, it checks the docs say so.

### 4. Report Review

Reviewers flag findings they could not confirm as `suspected` (they have no web access, and some issues resist static reading). Before reporting, resolve each: verify post-cutoff versions against a live source, confirm others by re-reading the code; keep anything still unresolved under **Suspected** as a question -- never silently dropped. Then load the `gitwise:github-conventions` and `praxis:workspace-patterns` skills, write the review as `gitwise:github-conventions`' `review-format.md` says, save it as the next numbered review in the branch's folder in the workspace (`.claude/workspace/<effort>/<branch folder>/<n>.md`; `praxis:workspace-patterns` says how to find it), show it to the user and give them the path. For a branch with no PR, name the base you diffed against at the top of the review.
