# Merge setting

Which text becomes the commit on the default branch depends on how the project merges. Before writing the PR title or the PR description, learn it from the first source that answers:

1. The project's statement, in its agent instruction files or CONTRIBUTING. A statement wins over what the repository's settings show: practice can differ from settings.
2. The repository's settings: `gh api repos/OWNER/REPO`. Without push or admin rights these fields read null; null means unknown, so go to the next source. The settings decide only when one merge method is enabled (`allow_squash_merge`, `allow_rebase_merge`, `allow_merge_commit`). For squash merges, `squash_merge_commit_title` and `squash_merge_commit_message` give the codes below; for merge commits, `merge_commit_message`.
3. The default branch. Take the newest squash commit of a PR with two or more commits (its subject ends "(#N)"). Blocks that open with "* " mean the branch's commit messages land. A body that matches that PR's description means the PR description lands. A subject with no body but trailers means only the PR title lands. A commit with two parents is a merge commit.
4. Ask the user.

What lands on the default branch (API codes in brackets):

- Squash, "Default message" (`COMMIT_OR_PR_TITLE` with `COMMIT_MESSAGES`), GitHub's default: the PR title, then every commit message on the branch, oldest first. A one-commit PR lands that commit's own subject and message. Merges from the base branch into the PR branch are left out. Write each commit message for a later reader of the default branch.
- Squash, "Pull request title and commit details" (`PR_TITLE` with `COMMIT_MESSAGES`): the same, for every PR.
- Squash, "Pull request title and description" (`PR_TITLE` with `PR_BODY`), or a bot that builds the commit from them: the PR title and the PR description. The PR description then carries the reasons; reviewer-only notes go in a PR comment.
- Squash, "Pull request title" (`PR_TITLE` with `BLANK`): the PR title only. The PR description, which "(#N)" leads to, holds the reasons.
- Merge commit: each commit message as its own commit, plus a merge commit whose message follows `merge_commit_message`: the PR title (`PR_TITLE`), the PR description (`PR_BODY`, which then also carries the reasons), or nothing (`BLANK`).
- Rebase merge, direct push: each commit message as its own commit.

A PR into a feature branch lands in that branch; what reaches the default branch is decided when the feature branch's own PR merges.

When the merge setting is still unknown and nobody can be asked:

- write every commit message to land, as under every setting;
- give the reasons in the commit messages and in the PR description;
- write a merge dependency in the PR description as a fact ("Requires #52.");
- put reading guidance and requests to the reviewer in a PR comment;
- say in that PR comment, not in the PR description, that the merge setting was not found.
