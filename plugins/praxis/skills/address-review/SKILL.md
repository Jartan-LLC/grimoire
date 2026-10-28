---
name: address-review
description: Work through review findings on a PR, or on a branch before it has one, one at a time
argument-hint: PR number or branch
---

# Address Review

Work through code review findings on a pull request, or on a branch before it has one, investigating each one and applying fixes where warranted.

**Always pause for the user's decision on each finding** -- even in auto mode, even if the reviewer or your own assessment recommends skipping. Auto mode grants tool access, not decision authority; the user decides what to fix, skip, or adjust.

Where the project's own rules say otherwise, follow them.

## Process

### 1. Load Review

Determine the PR number or branch from the user's request; with neither, the current branch. A branch with an open PR (`gh pr view <branch> --json number,state`) is handled as that PR. For a PR, get its branch (`gh pr view <pr-number> --json headRefName,isCrossRepository`). Load the `praxis:workspace-patterns` skill and read the latest review in the branch's folder in the workspace (the `<n>.md` with the highest number). For a PR, also read what people have posted on it: its comments and reviews, and the comments on its lines, which `gh pr view` does not show:

```bash
gh pr view <pr-number> --comments
gh api --paginate repos/{owner}/{repo}/pulls/<pr-number>/comments
```

If the saved review is missing, tell the user and ask where it is, or offer to run review-pr. Take each finding, from the saved review or posted, that no later commit, reply or line in the PR description has answered, and parse them into a numbered list grouped by severity (Critical > Important > Minor).

### 2. Check Out Branch

Ensure the branch is checked out locally so fixes can be applied. Load the `gitwise:commit-pr-writing` and `gitwise:github-conventions` skills. Check the PR title and description (`gh pr view <pr-number> --json title,body,baseRefName`; with no PR, the branch's `pr.md` and the base the review names) against `git diff <base>...HEAD`, update what no longer holds as `gitwise:commit-pr-writing` says (`gh pr edit <pr-number>`, or in `pr.md`, writing it if missing), and tell the user what you changed.

### 3. Walk Through Findings

Before a fix edits code, read `writing.md` in the `praxis:comment-hygiene` skill; before it edits a document, read that document's file in the `praxis:docs-patterns` skill (its SKILL.md maps each document to its file). Read them even when the skill is already loaded: they cover the comments and documents a fix writes and the ones it makes false.

Work through each finding sequentially. For each one:

1. **Investigate** -- Read the relevant code. Understand whether the finding is a real problem, a theoretical concern, or a false positive. Check how the rest of the codebase handles the same pattern.
2. **Assess** -- Present your assessment to the user: is it a real issue, valid but not applicable here, or wrong? Propose a specific fix or recommend skipping, with reasoning.
3. **Act on user decision** -- Apply the fix, skip it, or adjust based on the user's response.

Do NOT blindly apply every suggestion. Investigate first -- the reviewer may have missed context, flagged a pattern that's intentional, or suggested a fix that creates inconsistency with the rest of the codebase.

When the user agrees to skip a finding, note it and the reason (step 5).

### 4. Commit

The user may ask to commit at any point during the review -- commit what's been done so far and continue with the remaining findings. Write each commit message as `gitwise:commit-pr-writing` says. Never push unless the user explicitly asks.

### 5. Close the Round

Update the PR title and description, or `pr.md`, as in step 2. A declined finding, or a fix made differently than asked, is a decision a reviewer might question: give it its line there as `gitwise:commit-pr-writing` says.

Where a person posted a finding that the round declined, fixed differently or found already the case, reply to it with what was done and why: in its thread when it was posted on a line (`gh api repos/{owner}/{repo}/pulls/<pr-number>/comments/<comment-id>/replies -f body=...`, with the id of the thread's first comment: the finding's `in_reply_to_id` when it has one), otherwise in one PR comment for each review or comment that holds such findings. Answer nothing else on the PR.

For a PR whose round's commits are not pushed yet, tell the user the update and any reply are ready for after the push.
