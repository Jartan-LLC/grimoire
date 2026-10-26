Issue #58: `retry()` retries forever when `attempts=0`. Make 0 mean "no retries", with a test, commit it on
a new branch, and then write the PR title and description to `pr-draft.md` (no GitHub access here). The
backoff jitter is wrong too, but that's #59 and needs its own design, so don't touch it.
