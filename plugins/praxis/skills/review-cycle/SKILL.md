---
name: review-cycle
description: Take a branch through review rounds until two come back clean, then open its draft PR
argument-hint: Branch or branches (may include additional context)
---

# Review Cycle

Take a branch through rounds of review and fixes until two rounds in a row find nothing Critical or Important, then through a closing round on its words, then open its PR as a draft.

By invoking this command the user grants three things for the branches it names, or for the current branch when it names none: pushing each branch and updating its open PR's title and description after every round, the addresser's authority to decide findings (step 2), and opening each branch's draft PR, with the stack link `praxis:create-pr` adds (step 5). Nothing else: post nothing else to GitHub, and never force-push or rewrite a pushed commit, except to update a stack as `gitwise:github-conventions` says, which this grant covers.

A raised finding is a judgment call the addresser does not settle by fixing. By default each goes to the user (raise mode). When the user says they will not be around, or asks the cycle to decide, the addresser decides them instead (decide mode). Take the mode from the user's request; when it does not say, from `cycle.md` when resuming, else raise. Switch whenever the user says so.

Where the project's own rules say otherwise, follow them.

## Process

### 1. Set Up

Take the branches from the user's request; with none named, the current branch, as `praxis:review-pr` and `praxis:address-review` do. Load the `praxis:workspace-patterns` skill. For each branch, find or make its branch folder and a checkout of the branch: the one that has it, or a worktree, as `praxis:workspace-patterns` says. Never switch another checkout's branch. Take the base as `praxis:review-pr` does.

The branch folder's `cycle.md` holds the cycle's state: the mode, the round, how many clean rounds in a row, each raised finding with its recommendation and the user's answer, each finding left for the user, each reply waiting for the user, and the PR number once the PR opens. The PR text is `pr.md` while the branch has no open PR; once it has one, it is the PR's own title and description. If `cycle.md` records a cycle in progress, resume from it. Otherwise load the `gitwise:commit-pr-writing` skill, write `pr.md` as it says unless the branch has an open PR, and start `cycle.md`.

### 2. Run a Round

1. **Review.** Spawn a general-purpose agent, which can load skills and spawn agents (review-pr's own reviewer agents cannot), that runs `praxis:review-pr` on the branch in its checkout and saves the next numbered review in the branch folder. It reviews the whole branch against its base every round, never only the latest commit or the commits since the last round, unless the user's request limits it. Its brief gives the branch, the base, the checkout and the branch folder, and says: post nothing; read only, with no checkout, switch, reset, commit or push; read other commits with `git show <sha>:<path>`. It says nothing about earlier rounds or what to look for.
2. **Address.** Spawn a general-purpose agent as the addresser, which runs `praxis:address-review` on that review in the branch's checkout. Its brief says: the user has given you decision authority for this review through `/praxis:review-cycle`. The PR text is `pr.md` in the branch folder, or the PR's title and description once the branch has an open PR (`gh pr edit`). Post nothing else to GitHub: no replies in threads, no PR or review comments. Where address-review would reply to a finding a person posted, record the reply in `cycle.md` as waiting for the user instead. First carry out each answer the user gave in the branch folder's `cycle.md` that is not yet carried out: the fix, or, for a finding the user declined, a decision line in the PR text as `gitwise:commit-pr-writing` says; mark it carried out. Fix each finding that is minor or has one clear objective fix, and fix every instance of it in the change. Give each important or critical finding you decline, as wrong or not worth fixing, a decision line in the PR text with your reason, in either mode. Raise only an important or critical finding that is a real judgment call (policy, repo settings, public surface, what the project's rules make ask-first, destructive steps): record it in `cycle.md` with a recommendation, and leave it unfixed. In decide mode, carry out your recommendation instead, in a commit of its own, record it in `cycle.md` as decided with your reasoning, and give it a decision line in the PR text as `gitwise:commit-pr-writing` says; record anything outside the branch (repo settings, destructive steps) in `cycle.md` as left for the user, and leave it. A finding already in `cycle.md` is not recorded again. Write each finding's answer under it in the review. Check you are on the branch, then put the round's other fixes in one new commit, its message written as `gitwise:commit-pr-writing` says and checked against it. A commit message already pushed is corrected by a later commit that names it, never by rewriting.
3. **Verify and push.** Run the Verify commands from the agent instruction files, fix what fails in a new commit, and push the branch. When the branch has an open PR, then apply the PR title and description update the addresser held for after the push (`gh pr edit`).

### 3. Decide Whether to Stop

A round is clean when its review has nothing Critical or Important, at the reviewer's tier or a higher one the addresser gives by `praxis:review-severity`. Dismissing a finding does not make its round clean. A finding decided in decide mode or declined by the addresser or the user, with its decision line in the PR text, that a later round raises again without new evidence against that decision counts as answered: it does not break the clean streak. In decide mode, a finding left for the user in `cycle.md` does not break it either, whichever round raises it.

- In raise mode, tell the user each raised finding with its recommendation, and keep running rounds while it waits. An answer that changes code after the clean streak has started resets the streak.
- On a switch to decide mode, have the addresser decide the open raised findings; on a switch to raise mode, decided findings stay and remain listed for the user. Record the mode in `cycle.md`.
- Stop running review rounds, and go on to the closing round, when two rounds in a row are clean and no raised finding is open; in decide mode, a finding left for the user does not hold it open. The last round's Minor fixes, verified and pushed in step 2, get no round of their own.
- After a handful of rounds, tell the user how many have run. In raise mode, ask whether to go on; in decide mode, go on.

### 4. Run the Closing Round

Spawn a reviewer as in step 2, with `praxis:review-pr` limited to the documentation, comments, docstrings and commit messages the change adds, changes or makes false, and the PR title and description. Address it, verify and push as in step 2. If its fixes change code, the streak starts over: go back to step 2 until two rounds in a row are clean, then run the closing round again.

### 5. Open the Draft

Open the PR with `praxis:create-pr`, run in the branch's checkout with the issue from `pr.md`'s `Closes` line or the effort folder's name; it takes its title and description from `pr.md` and opens it as a draft. If the branch already has an open PR, skip create-pr and leave the PR's draft state as it is. Record the PR number in `cycle.md`, tell the user the PR is open, with each finding left for them first, then each reply waiting for them, then each finding decided in decide mode and its commit, then each Important or Critical finding the addresser declined, with its reason, and stop: the user marks it ready.

## Several Branches

- Run each branch's cycle on its own, and start its next round as soon as its last one is addressed, so rounds across branches stagger instead of running in waves.
- Each cycle reads and writes only its own branch folder and checkout.
- For a stack, start the upper branch's cycle after the lower one finishes, once the upper branch is synced onto the lower one as `gitwise:github-conventions` says. The lower branch's finished cycle counts as the lower PR's review being done, which github-conventions waits for before it opens the upper PR.
