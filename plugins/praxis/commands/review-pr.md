---
description: Review a pull request using specialized reviewer agents
argument-hint: PR number (may include additional context)
---

# Review PR

Review a pull request with category-based reviewer agents.

## Process

### 1. Get PR Context
Extract the PR number from `$ARGUMENTS` (the user may include additional context beyond just the number). Fetch the PR details and diff:
```bash
gh pr view <pr-number>
gh pr diff <pr-number>
```

### 2. Categorize and Review
Launch relevant reviewer agents based on changed files:
- Backend changes -> `backend-reviewer`
- Frontend changes -> `frontend-reviewer`
- Documentation changes, or code that changes public behavior -> `doc-reviewer`
- CI/test changes -> `test-reviewer`
- All changes -> `general-reviewer`

### 3. Verify Documentation
If code changed public behavior, `doc-reviewer` must run -- it owns doc-code mismatch.

### 4. Post Review
Reviewers have no web access, so verify each `suspected` post-cutoff finding against a live source and confirm or drop it. Then post the review as a PR comment following `review-format.md` in the `gitwise:github-conventions` skill:

```bash
gh pr comment <pr-number> --body "<review comment>"
```
