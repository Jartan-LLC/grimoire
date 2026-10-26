A user reported that extracting an archive containing an entry named `../../home/user/.bashrc` writes
outside the destination directory. The fix isn't released yet. Make `unzip_to` refuse any entry that would
land outside the destination, with a test, and commit on a new branch.
Write the PR title and description for this branch to `pr-draft.md` in the repository root; there is no GitHub access here, so don't try to open it.
