# Stacked Pull Requests

A stack is a chain of PRs, each based on the branch of the PR below it, linked on GitHub so they merge bottom up as one series. The project's own rules win where they speak.

## When to Stack

Stack a change on an open PR when it builds on that PR's unmerged work and waiting for the merge would stall it. Keep each PR small enough to review alone, and put what a change depends on in its own branch or one below it. Changes that do not depend on each other go in separate PRs off the base branch. A stack stays within one repository: it cannot span forks.

Every PR in a stack is held to the rules and required checks of the bottom PR's base, and workflows that run on pull requests into that branch run on every PR in the stack. A stack rooted on a branch those workflows skip, such as an integration branch, gets no CI.

## Building a Stack

- Branch from the lower PR's branch and base the PR on it. Start the upper branch once the PR below has finished review: a change to the lower PR after the upper branch exists means rebasing every branch above it ([Updating a Stack](#updating-a-stack)). While the PR below is still in review, stack on it only when waiting would stall the work, and tell the user that each change to it then means a restack.
- Root a stack on the branch it merges into, never on another stack's branch, and do not delete the branch a stack is based on while the stack is open. When that branch is deleted, GitHub moves the stack onto the default branch without rebasing it, and the bottom PR then carries every commit of the deleted branch.
- A chain of PRs is not a stack until it is linked, and until then the stack base's workflows do not run on the upper PRs. `gh api repos/{owner}/{repo}/pulls/<lower PR> --jq .stack` prints the lower PR's stack, with its `number` `<n>`, its `size` and the lower PR's `position`, or nothing for a PR in no stack. When the lower PR is its stack's top PR (`position` equals `size`), add the new PR to the stack:

  ```bash
  gh api -X POST repos/{owner}/{repo}/stacks/<n>/add --input - <<<'{"pull_requests": [<new PR>]}'
  ```

  GitHub adds PRs only above a stack's top PR, so when the lower PR sits below its stack's top, the new PR cannot join that stack: tell the user instead of linking it.

  When the lower PR is in no stack, create a stack from the chain, bottom first. Each PR's base must be the branch of the PR before it, or GitHub refuses with 422:

  ```bash
  gh api -X POST repos/{owner}/{repo}/stacks --input - <<<'{"pull_requests": [<bottom PR>, ..., <top PR>]}'
  ```

- The base of a PR in a stack cannot be edited. To change it, unstack first (`gh api -X POST repos/{owner}/{repo}/stacks/<n>/unstack`), which takes the open PRs out of the stack with their bases kept, then edit the base and link the stack again.

## Updating a Stack

When a PR in a stack changes after branches sit on it, commit the change on that PR's branch. Then, bottom up, rebase each branch above onto the branch below it and push it:

```bash
git rebase --onto <branch below> <old tip of branch below> <branch>
git push --force-with-lease origin <branch>
```

`<old tip of branch below>` is where that branch pointed before it changed or was rebased, so note each tip before you rebase. A stack that is not linear does not merge, even while each PR reports itself mergeable.

Restacking, here or after a merge ([Merging a Stack](#merging-a-stack)), is the one case where a pushed commit is rewritten: do it only with the approval the project requires for a force-push, or the user's where it states none. Where the `gh stack` extension is installed, `gh stack rebase --upstack` then `gh stack push` do the same, as does **Rebase stack** in the web UI, under the same approval.

## Merging a Stack

- Merging a PR in a stack also merges every unmerged PR below it, in one operation, and the PRs above stay open; under a squash merge each PR lands as its own commit. To merge a stack whose PRs are all ready, merge its top PR.
- None of the PRs being merged may be a draft: mark each ready first (`gh pr ready`).
- `gh pr merge` and the `pulls/<n>/merge` endpoint refuse a PR in a stack. Merge it with `gh stack merge <n> --yes --<squash|merge|rebase>` where `gh stack` is installed, or with the asynchronous merge endpoint and the PR's head commit (`gh pr view <n> --json headRefOid -q .headRefOid`), each given the method the project merges with. A person can also merge it in the web UI.

  ```bash
  gh api -X PUT repos/{owner}/{repo}/pulls/<n>/merge-async -f merge_method=<squash|merge|rebase> -f sha=<head sha> --jq .details.uuid
  ```

  Then poll `gh api repos/{owner}/{repo}/pulls/<n>/merge-async/<uuid>` until its `status` is `merged`; `enqueued`, when the base branch's merge queue took the PR and will merge it later (`gh pr view <n> --json state` shows when it has); or `failed`, with the reason in `details.message`.
- After a merge that leaves PRs above it open, GitHub retargets the next PR onto the stack's base and rebases the PRs above. Before merging the next one, check that it holds only its own commits (`gh pr view <n> --json commits`): one that was not rebased still carries the merged PR's commits, and under a squash merge their messages land a second time. If it carries them, restack it and the branches above it as [Updating a Stack](#updating-a-stack) says, onto the stack's base, with the merged PR's last head commit (`gh pr view <merged PR> --json headRefOid -q .headRefOid`) as `<old tip of branch below>`.
