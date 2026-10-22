---
name: review-pr
description: Review a pull request using specialized reviewer agents
argument-hint: PR number (may include additional context)
---

# Review PR

Review a pull request with category-based reviewer agents.

## Process

### 1. Get PR Context

Determine the PR number from the user's request, which may carry context beyond the number. Fetch the PR details and diff:

```bash
gh pr view <pr-number>
gh pr diff <pr-number>
gh pr view <pr-number> --json title,body,commits
```

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

Reviewers flag findings they could not confirm as `suspected` (they have no web access, and some issues resist static reading). Before reporting, resolve each: verify post-cutoff versions against a live source, confirm others by re-reading the code; keep anything still unresolved under **Suspected** as a question -- never silently dropped. Then load the `gitwise:github-conventions` skill, write the review as its `review-format.md` says, save it to `.claude/workspace/pr-<pr-number>-review.md` (replacing any earlier one), show it to the user and give them the path.
