---
name: recursive-implement
description: Implement a plan, issue or description without stopping to ask, splitting it across parallel subagents where that pays; leaves the work uncommitted and unreviewed.
argument-hint: Plan file path, issue number, or description
---

# Recursive Implement

Implement a plan, an issue or a description to completion in the main thread, splitting it across parallel subagents where that pays.

By invoking this command the user grants one thing: deciding without asking and running to completion. Nothing else: never commit, branch, push, open a PR, post to GitHub, run a code review, or take an action the project's rules say to ask about first. Build around such an action and list it under Left for the user.

Where the project's own rules say otherwise, follow them, but never past this grant.

## Process

### 1. Load the Skill

Load the `recursio:splitting-implementation` skill.

### 2. Take the Input

- **A plan file**, an old `wave-plan-*.md` included: read it.
- **An issue number**: run `gh issue view <number> --comments`, and read `.claude/workspace/issue-<number>/plan.md` if it exists.
- **A description**: take it as given.

Add the requirements discussed in the conversation, and read the project's rules and its Verify commands. If `split.md` in the effort's folder records waves already done, resume from the first wave whose barrier has not passed.

### 3. Split or Build

Act as the root in the main thread: split or build as the skill says. When splitting, write `split.md`, the contracts and the contract tests, then run the waves.

### 4. Update Docs and Changelog

Make the doc and changelog changes the project's rules say the change owes.

### 5. Verify

Run the project's Verify commands and fix what fails.

### 6. Report

Tell the user:

- what was built, and the test results;
- for each part: split, built or could not split;
- each decision taken without asking, and its source;
- what is left for the user;
- the path of `split.md`, if one was written;
- that the work is uncommitted and unreviewed.
