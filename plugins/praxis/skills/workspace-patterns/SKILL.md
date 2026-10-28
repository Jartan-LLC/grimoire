---
name: workspace-patterns
description: Where an agent keeps its working files -- plans, research, reviews, notes, state to resume from -- one folder per effort under the main checkout's .claude/workspace/, one subfolder per branch, and where worktrees go.
when_to_use: Writing or looking for a plan, review, research notes or other working file, resuming earlier work, or adding a git worktree.
user-invocable: false
---

# Workspace Patterns

Working files are what you write for yourself and the user while you work: plans, research, reviews,
notes, state to resume from. They are not project files, and no commit carries them.

Where the project's own rules say otherwise, follow them.

## The workspace

- The workspace is `.claude/workspace/` in the main checkout, also when you work in a worktree. In a
  linked worktree (`git rev-parse --git-dir` differs from `--git-common-dir`) the main checkout is the
  parent of `git rev-parse --path-format=absolute --git-common-dir`; anywhere else, submodules
  included, it is `git rev-parse --show-toplevel`. A worktree of a bare repository has no main
  checkout: ask the user where the workspace goes. A worktree's own `.claude/workspace/` goes when the
  worktree does. Outside git, it is `.claude/workspace/` in the
  project's root directory.
- Every working file goes in the workspace, never in the project root or beside the code.

## Layout

- One folder per effort: `issue-<n>` when the work has an issue, otherwise a short name chosen when the
  work starts, such as a topic or the branch name.
- In it, the effort's `plan.md`, research and notes, and one subfolder per branch for what belongs to
  that branch's change, its branch folder: the branch name with each `/` written as `--`
  (`feature/retry` -> `feature--retry`). For a PR from a fork, whose branch name another fork can
  share (`main`, `patch-1`), the branch folder is `pr-<n>`.
- Reviews of a branch are numbered by round in its subfolder: `1.md`, `2.md`, ... A new review takes the
  number after the highest (compare numbers, not names: `10.md` follows `9.md`) and leaves the earlier
  ones as they are.
- To find a branch's folder, look for one first: `.claude/workspace/*/<branch folder>/`. Failing
  that, make it in the folder of the issue the PR closes (`gh pr view <n> --json
  closingIssuesReferences`) or the work is for, and failing that, in a new effort folder.
- Finished efforts move to `.claude/workspace/archive/`; look there when resuming old work.
- When a file you expect is missing, look for one that serves before saying there is none: earlier
  versions of praxis's plan-issue and review-pr wrote plans as `.claude/workspace/issue-<n>-plan.md`
  and reviews as `.claude/workspace/pr-<n>-review.md`; look there too. Write new files only where this
  layout puts them.

## Worktrees

Add a worktree at `.claude/worktrees/<branch>` in the main checkout, with each `/` in the branch written
as `--`. First check `git worktree list`: a checkout that already has the branch serves.

## When git does not ignore them

Before the first write to the workspace or a worktree, check that git ignores the path you write
(`git check-ignore -q <path>`). If it does not, ask the user before changing `.gitignore`, and offer
`.git/info/exclude`, which changes no tracked file. Until they answer, stage files by name, never with
`git add -A` or `git add .`.
