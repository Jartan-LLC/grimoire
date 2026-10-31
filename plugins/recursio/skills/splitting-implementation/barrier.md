# Barrier checklist

Run it once every part of the wave has reported (at the root, every part listed under the wave in split.md), in this order.

1. **Scope.** Every file changed since the wave's snapshot (new to `git status --porcelain -uall`, gone from it, or with a different hash) lies in exactly one part's scope, and that part reported it. Files under `.claude/workspace/`, such as split.md, are the level's own and exempt. A file in no scope or in two is a stray or overlapping write: treat it as a failure (step 6).
2. **Contracts.** Every contract file and contract test matches the hash recorded before the wave. Restore a changed one from its recorded hash (`git cat-file -p <hash>`), and treat the part that changed it as failed.
3. **Tests.** Run the contract tests, then the full relevant suite, on the combined tree. Parts can pass alone and fail together.
4. **Objective.** Check the level's own objective: at the root, an end-to-end or behavioural check against the request; below it, the contract in the level's brief. Low-level checks miss a broken feature.
5. **Divergence.** Compare siblings for choices no settled decision covered, such as naming, error shape or a duplicated helper. Pick one answer, fix the others, record it as a settled decision, and pass a short note of it into later waves' briefs.
6. **Failure.** Retry a failed part at most twice, with the failing output itself in its brief, not a paraphrase. Then split it differently. Then report up; at the root, list it under Left for the user.
7. **Record.** At the root, write the barrier's result in split.md: the commands run and their outcome, each divergence settled, each retry, and each part's status. A part that split puts the same in its report.

Code review is not the barrier's job.
