# Stacked Pull Requests

A stack is a chain of PRs, each based on the branch of the PR below it, linked on GitHub so they merge bottom up as one series. The project's own rules win where they speak.

## When to Stack

Stack a change on an open PR when it builds on that PR's unmerged work and waiting for the merge would stall it. Keep each PR small enough to review alone, and put what a change depends on in its own branch or one below it. Changes that do not depend on each other go in separate PRs off the base branch. A stack stays within one repository: it cannot span forks.

Every PR in a stack is held to the rules and required checks of the bottom PR's base, and workflows that run on pull requests into that branch run on every PR in the stack. A stack rooted on a branch those workflows skip, such as an integration branch, gets no CI.

## Building a Stack

- Branch from the lower PR's branch and base the PR on it. Start the upper branch once the PR below has finished review: a change to the lower PR after that means rebasing every branch above it ([Updating a Stack](#updating-a-stack)).
- Root a stack on the branch it merges into, never on another stack's branch, and do not delete the branch a stack is based on while the stack is open. When that branch is deleted, GitHub moves the stack onto the default branch without rebasing it, and the bottom PR then carries every commit of the deleted branch.
- A chain of PRs is not a stack until it is linked, and until then the stack base's workflows do not run on the upper PRs. When the lower PR is in a stack (`gh api repos/{owner}/{repo}/pulls/<lower PR> --jq .stack.number` prints its number `<n>`), add the new PR to it:

  ```bash
  gh api -X POST repos/{owner}/{repo}/stacks/<n>/add --input - <<<'{"pull_requests": [<new PR>]}'
  ```

  Otherwise create a stack from the chain, bottom first. Each PR's base must be the branch of the PR before it, or GitHub refuses with 422:

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

This is the one case where a pushed commit is rewritten: do it only with the approval the project requires for a force-push, or the user's where it states none. Where the `gh stack` extension is installed, `gh stack rebase --upstack` then `gh stack push` do the same, as does **Rebase stack** in the web UI, under the same approval.

## Merging a Stack

- Merging a PR in a stack also merges every unmerged PR below it, in one operation, and the PRs above stay open; under a squash merge each PR lands as its own commit. To merge a stack whose PRs are all ready, merge its top PR.
- None of the PRs being merged may be a draft: mark each ready first (`gh pr ready`).
- `gh pr merge` and the `pulls/<n>/merge` endpoint refuse a PR in a stack. Merge it in the web UI, with `gh stack merge` where `gh stack` is installed, or with the asynchronous merge endpoint, giving the method the project merges with and the PR's head commit (`gh pr view <n> --json headRefOid -q .headRefOid`):

  ```bash
  gh api -X PUT repos/{owner}/{repo}/pulls/<n>/merge-async -f merge_method=<squash|merge|rebase> -f merge_action=direct_merge -f sha=<head sha> --jq .details.uuid
  ```

  Then poll `gh api repos/{owner}/{repo}/pulls/<n>/merge-async/<uuid>` until its `status` is `merged`, or `failed` with the reason in `details.message`.
- After a merge that leaves PRs above it open, GitHub retargets the next PR onto the stack's base and rebases the PRs above. Before merging the next one, check that it holds only its own commits (`gh pr view <n> --json commits`): one that was not rebased still carries the merged PR's commits, and under a squash merge their messages land a second time. A PR description gives no rebase step for after its merge.
