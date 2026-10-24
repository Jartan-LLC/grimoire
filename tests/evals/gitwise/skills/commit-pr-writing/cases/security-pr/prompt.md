A user reported that `read_doc("../../etc/passwd")` returns the system's password file instead of failing.
The fix isn't released yet. Make `read_doc` refuse any name that resolves outside the docs root, with a
test, and commit on a new branch.
Write the PR title and description for this branch to `pr-draft.md` in the repository root; there is no GitHub access here, so don't try to open it.
