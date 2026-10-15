---
name: address-review
description: Work through review findings on a PR one at a time
argument-hint: PR number
---

# Address Review

Work through code review findings on a pull request, investigating each one and applying fixes where warranted.

**Always pause for the user's decision on each finding** -- even in auto mode, even if the reviewer or your own assessment recommends skipping. Auto mode grants tool access, not decision authority; the user decides what to fix, skip, or adjust.

Where the project's own rules say otherwise, follow them.

## Process

### 1. Load Review

Determine the PR number from the user's request. Fetch the review comments:

```bash
gh pr view <pr-number> --comments
```

There may be multiple review comments in the history -- use only the most recent one. Parse its findings into a numbered list grouped by severity (Critical > Important > Minor).

### 2. Check Out Branch

Ensure the PR's branch is checked out locally so fixes can be applied. Then check the PR title and description once, as step 5 describes.

### 3. Walk Through Findings

Work through each finding sequentially. For each one:

1. **Investigate** -- Read the relevant code. Understand whether the finding is a real problem, a theoretical concern, or a false positive. Check how the rest of the codebase handles the same pattern.
2. **Assess** -- Present your assessment to the user: is it a real issue, valid but not applicable here, or wrong? Propose a specific fix or recommend skipping, with reasoning.
3. **Act on user decision** -- Apply the fix, skip it, or adjust based on the user's response.

Do NOT blindly apply every suggestion. Investigate first -- the reviewer may have missed context, flagged a pattern that's intentional, or suggested a fix that creates inconsistency with the rest of the codebase.

When the user agrees to skip a finding, post a brief PR comment explaining why it was declined:

```bash
gh pr comment <pr-number> --body "**Re: <finding title>** -- <concise reason for skipping>"
```

### 4. Commit

The user may ask to commit at any point during the review -- commit what's been done so far and continue with the remaining findings. Write the message as for any commit on the branch, for a later reader of the default branch:

- The subject names the change this commit makes, in the project's commit format (see `gitwise:github-conventions`) -- never "address review findings".
- The body gives the reason and the technical detail in terms of the code as this commit leaves it. No list of changed files, and no mention of the review or its rounds.
- If the commit makes false something an earlier commit message in this PR states (check `git log --reverse --format=%B <base>..HEAD`), its first paragraph names that statement and why it changed, with the corrected action where the earlier message gave one.

While a commit is not yet pushed, fold a further fix to the same change into it (`git commit --amend` for the last commit) instead of adding a commit. Never rewrite a pushed commit.

Put the finding-by-finding answers in one PR comment for the round, not in the commit message. After committing, check that the PR title still names the whole change; if not, update it (`gh pr edit <pr-number> --title "<title>"`) or tell the user. Never push unless the user explicitly asks.

### 5. Refresh the PR Title and Description

At the start of the task (step 2) and after each round's commits are pushed, compare the PR title and description (`gh pr view <pr-number> --json title,body`) with `git diff <base>...HEAD`, and fix what no longer holds (`gh pr edit <pr-number>`). Start from the current text, keep what a person added, and tell the user what you changed. If the round's commits are not pushed yet, tell the user the PR title and description need this check after the push.

Where the PR description becomes the squash commit's message (see `gitwise:github-conventions`), rewrite the PR title and description to describe the head commit before asking for another review: the final design first, each dropped design as a rejected alternative with its reason, and nothing about the review or its rounds.
