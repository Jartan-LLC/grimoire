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
```

### 2. Categorize and Review

Launch relevant reviewer agents based on changed files:

- Backend changes -> `backend-reviewer`
- Frontend changes -> `frontend-reviewer`
- Documentation changes, or code that changes public behavior -> `doc-reviewer`
- CI/test changes -> `test-reviewer`
- Non-trivial code changes -> `structure-reviewer`
- All changes -> `general-reviewer`

### 3. Verify Documentation

If code changed public behavior, `doc-reviewer` must run -- it owns doc-code mismatch.

### 4. Post Review

Reviewers flag findings they could not confirm as `suspected` (they have no web access, and some issues resist static reading). Before posting, resolve each: verify post-cutoff versions against a live source, confirm others by re-reading the code; post anything still unresolved under **Suspected** as a question -- never silently dropped. Then post the review as a PR comment following `review-format.md` in the `gitwise:github-conventions` skill, ending with the reply hint `-- reply with /praxis:address-review <pr-number> to work through findings`:

```bash
gh pr comment <pr-number> --body "<review comment>"
```
