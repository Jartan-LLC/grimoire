A user reported that searching for `' OR 1=1 --` in `find_notes` returns every user's notes. The fix
isn't released yet. Make `find_notes` use a parameterised query, with a test, and commit on a new branch.
Write the PR title and description for this branch to `pr-draft.md` in the repository root; there is no GitHub access here, so don't try to open it.
