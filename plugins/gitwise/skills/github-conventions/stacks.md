# Stacked Pull Requests

A stack is a chain of PRs, each based on the branch of the PR below it, linked on GitHub so they merge bottom up as one series. The project's own rules win where they speak.

## Rules

1. Stack only a change that needs the open PR below it. Changes that do not depend on each other go in separate PRs off the base branch.
2. Cut and push the upper branch early, so its work is not held in a session's context, but open and link its PR only once the lower PR's review is done: first sync the upper branch onto the final lower branch once ([Updating a Stack](#updating-a-stack)), instead of carrying each lower-PR review fix up into it, then open and link the PR. If the lower PR has merged by then, restack the upper branch by the same steps, with the branch the lower PR merged into as the branch below and the lower PR's last head as the old tip, and base its PR on that branch, with no stack to link.
3. Test what lands. Merge a stack only by a PR that has passed the checks the project requires before a merge, as reported on that PR, run on what that merge lands against the base as it is now: after the base moves, that takes a new head, because re-running a check re-tests the old one. Merge a linked stack by its top PR, in one operation; a partial merge holds the PR it merges by to the same rule. When the project's checks do not run on what the merge lands, do not merge: tell the user.

## Linked Stacks and Unlinked Chains

A chain of PRs is not a stack until it is linked. Merging a PR in a linked stack also merges every unmerged PR below it, in one operation, and leaves the PRs above open; `gh pr merge` refuses it. In an unlinked chain each PR merges alone and `gh pr merge` works; after a merge the next PR is retargeted by hand unless GitHub retargets it when the merged PR's branch is deleted, then updated by hand (restack it as [Updating a Stack](#updating-a-stack) says, with the merged PR's last head as the old tip).

## Building a Stack

- Branch from the lower PR's branch and push it. Root the stack on the branch it merges into, never on another stack's branch, and do not delete a stack's base branch while the stack is open: GitHub then moves the stack onto the default branch without rebasing it, and the bottom PR carries every commit of the deleted branch.
- Never stack a sub-issue PR on its parent feature branch's PR: linking it would make its merge also merge the parent PR. Sub-issues that build on each other may stack within the parent branch, with the bottom PR based on it. A stack cannot span forks.
- Open the PR based on the lower PR's branch, then link it. `gh api repos/{owner}/{repo}/pulls/<lower PR> --jq .stack` prints the lower PR's stack `number`, `size` and `position`, or an empty line when it is in no stack. When `position` equals `size`, add the new PR:

  ```bash
  gh api -X POST repos/{owner}/{repo}/stacks/<number>/add --input - <<<'{"pull_requests": [<new PR>]}'
  ```

  When the lower PR is below its stack's top, GitHub cannot add the new PR: tell the user. When the lower PR is in no stack, create one, bottom first. Each PR's base must be the branch of the PR before it, or GitHub refuses with 422:

  ```bash
  gh api -X POST repos/{owner}/{repo}/stacks --input - <<<'{"pull_requests": [<bottom PR>, ..., <top PR>]}'
  ```

- A stacked PR's base cannot be edited. Unstack first (`gh api -X POST repos/{owner}/{repo}/stacks/<number>/unstack`; the open PRs keep their bases), edit the base, and link again.

## Updating a Stack

When a branch with branches stacked above it changes, from this session or elsewhere, restack them by these steps; a sync and the merge cases below use them too. They rewrite pushed commits, which updating a stack needs; where the project's rules require approval for a force-push, get it first. **Rebase stack** in the web UI does the same.

`gh api repos/{owner}/{repo}/stacks/<number> --jq '.pull_requests[].head.ref'` lists a stack's branches, bottom first.

1. Push your own commits, on whichever of the stack's branches they are, then run `git fetch origin`.
2. Before you move anything, note for each branch above the changed one the old tip of the branch below it: `git merge-base origin/<branch below> origin/<branch>`, or, where the PR below it has merged, that PR's last head (`gh pr view <n> --json headRefOid -q .headRefOid`; `git fetch origin pull/<n>/head` fetches it once its branch is gone). Stop and tell the user where a branch's local copy has commits its remote lacks (`git rev-list origin/<branch>..<branch>` lists any), or where `git log --oneline <old tip>..origin/<branch>` lists commits that are not that branch's own: a branch below it was rewritten, and its old tip is gone. Stop and tell the user, too, where `git status --porcelain` prints anything in a worktree you will run step 3 in: `git switch` would carry its uncommitted changes across.
3. Bottom up, start each branch above from its remote, rebase it onto the branch below as pushed, and push it. Where another worktree has the branch checked out, run its commands in that worktree:

   ```bash
   git switch -C <branch> origin/<branch>
   git rebase --onto origin/<branch below> <old tip of branch below> <branch>
   git push --force-with-lease origin <branch>
   ```

   If a rebase stops on a conflict, resolve it only where the resolution keeps both sides' changes as they were, such as two changelog entries; otherwise run `git rebase --abort` and tell the user.

   Afterwards, switch back to the branch you started on.

A stack that is not linear does not merge, even while each PR reports itself mergeable.

## Merging a Stack

- Mark every PR being merged ready first (`gh pr ready`): a draft among them fails the merge.
- `gh pr merge` and the `pulls/<n>/merge` endpoint refuse a stacked PR. Use the asynchronous merge endpoint with the PR's head commit (`gh pr view <n> --json headRefOid -q .headRefOid`) and the project's merge method, or let a person merge in the web UI:

  ```bash
  gh api -X PUT repos/{owner}/{repo}/pulls/<n>/merge-async -f merge_method=<squash|merge|rebase> -f sha=<head sha> --jq .details.uuid
  ```

  Poll `gh api repos/{owner}/{repo}/pulls/<n>/merge-async/<uuid>` until `status` is `merged` or `failed`. On `failed`, read `details.message`: restack a stack that needs rebasing ([Updating a Stack](#updating-a-stack)); otherwise tell the user.
- Before a partial merge, note the next PR's head (`gh pr view <n> --json headRefOid -q .headRefOid`). After it, GitHub retargets the next PR onto the stack's base and rebases the PRs above: wait until `gh pr view <n> --json baseRefName,headRefOid` shows the new base and a new head, or for two minutes if the head does not change. The next PR must then hold only its own commits (`gh pr view <n> --json commits`): one that still carries the merged PR's commits would land their messages a second time under a squash merge. Restack one that does ([Updating a Stack](#updating-a-stack)), with the stack's base as the branch below it.
