---
name: review-cycle
description: Take a branch through review rounds until two come back clean, then open its draft PR
argument-hint: Branch or branches (may include additional context)
---

# Review Cycle

Take a branch through rounds of review and fixes until two rounds in a row find nothing Critical or Important, then through a closing round on its words, then open its PR as a draft.

By invoking this command the user grants two things for the branches it names: pushing each branch after every round, and the addresser's authority to decide findings (step 2). Nothing else: post nothing to GitHub before the PR opens, and never force-push or rewrite a pushed commit.

A raised finding is a judgment call the addresser does not settle by fixing. By default each goes to the user (raise mode). When the user says they will not be around, or asks the cycle to decide, the addresser decides them instead (decide mode). Take the mode from the user's request, raise when it does not say, and switch whenever the user says so.

Where the project's own rules say otherwise, follow them.

## Process

### 1. Set Up

Load the `praxis:workspace-patterns` skill. For each branch, find or make its branch folder and a checkout of the branch: the one that has it, or a worktree, as `praxis:workspace-patterns` says. Never switch another checkout's branch. Take the base as `praxis:review-pr` does.

The branch folder's `cycle.md` holds the cycle's state: the mode, the round, how many clean rounds in a row, each raised finding with its recommendation and the user's answer, and the PR number once the PR opens. If it records a cycle in progress, resume from it. Otherwise load the `gitwise:commit-pr-writing` skill, write the branch's `pr.md` as it says (or take the title and description from the branch's open PR), and start `cycle.md`.

### 2. Run a Round

1. **Review.** Spawn a reviewer agent that runs `praxis:review-pr` on the branch in its checkout and saves the next numbered review in the branch folder. It reviews the whole branch against its base every round, never only the latest commit or the commits since the last round, unless the user's request limits it. Its brief gives the branch, the base, the checkout and the branch folder, and says: post nothing; read only, with no checkout, switch, reset, commit or push; read other commits with `git show <sha>:<path>`. It says nothing about earlier rounds or what to look for.
2. **Address.** Spawn an addresser agent that runs `praxis:address-review` on that review in the branch's checkout. Its brief says: the user has given you decision authority for this review through `/praxis:review-cycle`. Fix each finding that is minor or has one clear objective fix, and fix every instance of it in the change. Raise only an important finding that is a real judgment call (policy, repo settings, public surface, what the project's rules make ask-first, destructive steps): record it in the branch folder's `cycle.md` with a recommendation, and leave it unfixed. In decide mode, carry out your recommendation instead, in a commit of its own, record it in `cycle.md` as decided with your reasoning, and give it a decision line in `pr.md` as `gitwise:commit-pr-writing` says; leave anything outside the branch (repo settings, destructive steps) for the user. Write each finding's answer under it in the review. Check you are on the branch, then put the round's fixes in one new commit, its message written as `gitwise:commit-pr-writing` says and checked against it. A commit message already pushed is corrected by a later commit that names it, never by rewriting.
3. **Verify and push.** Run the Verify commands from the agent instruction files, fix what fails, and push the branch.

### 3. Decide Whether to Stop

A round is clean when its review has nothing Critical or Important, at the reviewer's tier or a higher one the addresser gives by `praxis:review-severity`. Dismissing a finding does not make its round clean. A finding already decided, with its decision line in `pr.md`, that a later round raises again without new evidence against that decision counts as answered: it does not break the clean streak.

- In raise mode, tell the user each raised finding with its recommendation, and keep running rounds while it waits. An answer that changes code after the clean streak has started resets the streak.
- On a switch to decide mode, have the addresser decide the open raised findings; on a switch to raise mode, decided findings stay and remain listed for the user. Record the mode in `cycle.md`.
- Stop when two rounds in a row are clean and no raised finding is open. Fix the last round's Minors without another round.
- After a handful of rounds, tell the user how many have run. In raise mode, ask whether to go on; in decide mode, go on.

### 4. Run the Closing Round

Spawn a reviewer as in step 2, with `praxis:review-pr` limited to the documentation, comments, docstrings and commit messages the change adds, changes or makes false, and the PR description. Address it, verify and push as in step 2. If the fixes change code, go back to step 2 until two rounds in a row are clean again.

### 5. Open the Draft

Open the PR with `praxis:create-pr`, which takes its title and description from `pr.md` and opens it as a draft. If the branch already has an open PR, update its title and description from `pr.md` instead (`gh pr edit`). Record the PR number in `cycle.md`, tell the user the PR is open, with each finding decided in decide mode and its commit, and stop: the user marks it ready.

## Several Branches

- Run each branch's cycle on its own, and start its next round as soon as its last one is addressed, so rounds across branches stagger instead of running in waves.
- Each cycle reads and writes only its own branch folder and checkout.
- For a stack, finish the lower branch's cycle before cutting the next branch.
