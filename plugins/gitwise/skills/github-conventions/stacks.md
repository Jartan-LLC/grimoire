# Stacked Pull Requests

A stack is a chain of PRs, each based on the branch of the PR below it, linked on GitHub so they merge bottom up as one series. The project's own rules win where they speak.

## Rules

1. Stack only a change that needs the open PR below it. Changes that do not depend on each other go in separate PRs off the base branch.
2. Cut and push the upper branch early, so its work and notes (its plan and PR notes in the workspace) are not held in a session's context, but open and link its PR only once the lower PR's review is done: first sync the upper branch onto the final lower branch once ([Updating a Stack](#updating-a-stack)), instead of carrying each lower-PR review fix up into it, then open and link the PR. If the lower PR has merged by then, restack the upper branch by the same steps, with the branch the lower PR merged into as the branch below and the lower PR's last head as the old tip, and base its PR on that branch, with no stack to link.
3. Test what lands. Merge a stack only after CI has passed on the PR you merge it by, against the stack's base as it is now: that PR's head holds everything the merge lands, and a base that moved after the run needs a fresh run, which only a new head brings (a restack, or an update of the branch): re-running the old workflow run re-tests the old merge commit. Merge a linked stack by its top PR, in one operation; a partial merge applies the same rule to the PR it merges by. When the project's CI does not test that PR, as when CI runs only on the bottom of a stack or the chain is unlinked, do not merge until the PR you merge by has a passing CI run, and tell the user if it gets none. To get one, do one of these:
   - Link an unlinked chain ([Building a Stack](#building-a-stack)).
   - Fold the stack into its bottom PR, so that PR holds every layer and its CI run tests what lands. Where the project has no convention for folding, the user decides how.
   - Ask the user to change CI.

## Linked Stacks and Unlinked Chains

A chain of PRs is not a stack until it is linked. Merging a PR in a linked stack also merges every unmerged PR below it, in one operation, and leaves the PRs above open; `gh pr merge` refuses it. Every PR in a linked stack is held to the rules and required checks of the stack's base, and the workflows that run on pull requests into that base run on every PR in it. In an unlinked chain each PR merges alone and `gh pr merge` works, but the base's workflows skip each PR above the bottom one until it is retargeted onto the base, and after a merge the next PR is updated by hand, and retargeted by hand unless GitHub retargets it when the merged PR's branch is deleted. A stack rooted on a branch those workflows skip, such as an integration branch, gets no CI.

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

When a branch with branches stacked above it changes, from this session or elsewhere, restack them by these steps; a sync and the merge cases below use them too. They rewrite pushed commits: run them only with the approval the project requires for a force-push, or the user's where it states none. **Rebase stack** in the web UI needs the same approval.

`gh api repos/{owner}/{repo}/stacks/<number> --jq '.pull_requests[].head.ref'` lists a stack's branches, bottom first.

1. Push your own commits, on whichever of the stack's branches they are, then run `git fetch origin`.
2. Before you move anything, note for each branch above the changed one the old tip of the branch below it: `git merge-base origin/<branch below> origin/<branch>`, or, where the PR below it has merged, that PR's last head (`gh pr view <n> --json headRefOid -q .headRefOid`; `git fetch origin pull/<n>/head` fetches it once its branch is gone). Stop and tell the user where a branch's local copy has commits its remote lacks (`git rev-list origin/<branch>..<branch>` lists any), or where `git log --oneline <old tip>..origin/<branch>` lists commits that are not that branch's own: a branch below it was rewritten, and its old tip is gone.
3. Bottom up, start each branch above from its remote, rebase it onto the branch below as pushed, and push it:

   ```bash
   git switch -C <branch> origin/<branch>
   git rebase --onto origin/<branch below> <old tip of branch below> <branch>
   git push --force-with-lease origin <branch>
   ```

A stack that is not linear does not merge, even while each PR reports itself mergeable.

## Merging a Stack

- Mark every PR being merged ready first (`gh pr ready`): a draft among them fails the merge.
- `gh pr merge` and the `pulls/<n>/merge` endpoint refuse a stacked PR. Use the asynchronous merge endpoint with the PR's head commit (`gh pr view <n> --json headRefOid -q .headRefOid`) and the project's merge method, or let a person merge in the web UI:

  ```bash
  gh api -X PUT repos/{owner}/{repo}/pulls/<n>/merge-async -f merge_method=<squash|merge|rebase> -f sha=<head sha> --jq .details.uuid
  ```

  Poll `gh api repos/{owner}/{repo}/pulls/<n>/merge-async/<uuid>` until `status` is `merged` or `failed`. On `failed`, read `details.message`: restack a stack that needs rebasing ([Updating a Stack](#updating-a-stack)); otherwise tell the user.
- Before a partial merge, note the next PR's head (`gh pr view <n> --json headRefOid -q .headRefOid`). After it, GitHub retargets the next PR onto the stack's base and rebases the PRs above: wait until `gh pr view <n> --json baseRefName,headRefOid` shows the new base and a new head, or for two minutes if the head does not change. The next PR must then hold only its own commits (`gh pr view <n> --json commits`): one that still carries the merged PR's commits would land their messages a second time under a squash merge. Restack it ([Updating a Stack](#updating-a-stack)), with the stack's base as the branch below it.
