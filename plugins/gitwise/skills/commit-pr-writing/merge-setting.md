# Merge setting

Which text becomes the commit on the default branch depends on how the project merges. The first source that answers gives the setting:

1. The project's statement, in its agent instruction files or CONTRIBUTING. A statement wins over what the repository's settings show: practice can differ from settings.
2. The repository's settings: `gh api repos/OWNER/REPO`. Without push or admin rights these fields read null; null means unknown, so go to the next source. The settings decide only when one merge method is enabled (`allow_squash_merge`, `allow_rebase_merge`, `allow_merge_commit`). For squash merges, `squash_merge_commit_title` and `squash_merge_commit_message` give the codes below; for merge commits, `merge_commit_message`.
3. The default branch. Take the newest squash commit of a PR with two or more commits (its subject ends "(#N)"). Blocks that open with "* " mean the branch's commit messages land. A body that matches that PR's description means the PR description lands. A subject with no body but trailers means only the PR title lands. A commit with two parents is a merge commit.
4. Ask the user.

What lands on the default branch (API codes in brackets), and what changes from the PR lines in [SKILL.md](SKILL.md):

- Squash, "Default message" (`COMMIT_OR_PR_TITLE` with `COMMIT_MESSAGES`), GitHub's default: the PR title, then every commit message on the branch, oldest first. A one-commit PR lands that commit's own subject and message. Merges from the base branch into the PR branch are left out. SKILL.md's lines apply as written.
- Squash, "Pull request title and commit details" (`PR_TITLE` with `COMMIT_MESSAGES`): the same, for every PR.
- Squash, "Pull request title and description" (`PR_TITLE` with `PR_BODY`), or a bot that builds the commit from them: the PR title and the PR description. Write the PR description as that commit message: start from `git log <base>..HEAD` and the final diff (for a single-commit PR, from that commit's message); give the reasons, and write the intent, flags and verification as facts; nothing about the review or its rounds; each paragraph on one unwrapped line; no template comments or placeholder. It describes the whole change as of the last commit: the final design first, each dropped design as a rejected alternative with its reason. Where to start reading, the "Changed in review" and "Declined from review" lines and other notes for the reviewer go in a PR comment.
- Squash, "Pull request title" (`PR_TITLE` with `BLANK`): the PR title only. Give the reasons in the PR description, which "(#N)" leads to, as well as in the commit messages.
- Merge commit: each commit message as its own commit, plus a merge commit whose message follows `merge_commit_message`: the PR title (`PR_TITLE`), the PR description (`PR_BODY`, written as under "Pull request title and description"), or nothing (`BLANK`).
- Rebase merge, direct push: each commit message as its own commit.

A PR into a feature branch lands in that branch; what reaches the default branch is decided when the feature branch's own PR merges.

When the merge setting is still unknown and nobody can be asked, SKILL.md's lines apply, except:

- give the reasons in the PR description as well as in the commit messages;
- put where to start reading, the "Changed in review" and "Declined from review" lines and requests to the reviewer in a PR comment;
- say in that PR comment, not in the PR description, that the merge setting was not found.
