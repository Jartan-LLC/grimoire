Write the PR title and description for this branch to `pr-draft.md` in the repository root; there is no GitHub access here, so don't try to open it.
During review, Sam asked me to make `slugify` fall back to "untitled" for empty results; I kept the empty string because callers already handle it. Dana asked for a test of text that is all punctuation, which I added in the last commit.
