---
name: commit-pr-writing
description: What a commit message, a PR title and a PR description say, and which of them lands on the default branch under GitHub's default squash merge.
when_to_use: Writing or updating a commit message, a PR title or a PR description, or reviewing one.
user-invocable: false
---

# Commit Messages and PR Descriptions

The project's own rules win where they speak. No style or brevity pass over a commit message or a PR description: keep every verification line, issue id and reason.

Before you state how the code behaves when it runs (its output, what a test catches, why a result comes out as it does), run it or watch it. If you only reasoned it out, check it now or leave it out. This does not apply to what the change does or why you chose it.

## The Commit Message

Write every commit message to land on the default branch, whatever the merge setting. Under GitHub's default squash merge, every commit message on the branch goes into the squash commit's message (merges from the base branch aside).

- Say why the change was made and why this way; where alternatives were weighed, name the one a later reader would propose and why it lost.
- Describe the change as merged; narrate no review rounds, requests, attempts, CI re-runs or branch history, and let the subject name the change (never "address review findings").
- Do not restate what the reader already has open: no file lists, diff retelling or test totals CI shows.
- State each gap or deferral (with its issue), deliberate omission (with its reason) and hazard a later edit must avoid in the commit message that makes the change. A one-time action only contributors owe (rebuild the dev container) goes in its first paragraph.
- A commit that reverses or replaces an earlier commit's statement or design names that statement or design by the earlier commit's subject, never "the previous commit", in its first paragraph, says why it was not enough, and gives the corrected action. The branch's earlier messages: `git log --reverse --format=%B <base>..HEAD`.
- A commit that only corrects what this PR added (a typo, a lint, a comment it now drops) takes a subject stating the merged result and no body.
- Make every "every", "all" or "no longer" true of the change as merged, or name the exception.
- A statement that a file was generated holds for its source as merged: a later commit that edits that source regenerates the file or says it predates the edit.

## The PR Title and Description

The lines below assume GitHub's default squash merge, where the commit messages land and the PR description does not. If the project's agent instruction files or CONTRIBUTING state another merge setting, follow it. Where that setting lands the PR description, write the description as the commit message for the whole branch: give the reasons, put any one-time action for contributors in its first paragraph rather than at the end, and leave out where to start reading.

The PR title names one change, as a commit subject in the project's commit format (`gitwise:github-conventions`): for a PR with two or more commits it becomes the squash commit's subject.

The PR description:

- Open with any merge dependency as a fact ("Requires #52."), then what the change does and why, in a sentence or two.
- One line per flag a careful reviewer could miss and per decision they might question, a change they would propose that you rejected included, each with its reason and stated as a fact about the change: "The parser keeps its old name, because the Codex mirror imports it." Do not say which review or request prompted a decision. Name any PR you took code from.
- Say where to start reading: the file, function or commit subject holding the core logic.
- State verification as results: what ran, what it showed, what was not run. No checkboxes or pasted output.
- Do not retell the commit messages or the diff beyond that opening and the flag and decision lines with their reasons.
- End with what the merger or contributors must do, or that merging is all.

To update a PR title or description, start from the current text, keep what a person added, and make both hold for the whole change as of the last commit.
