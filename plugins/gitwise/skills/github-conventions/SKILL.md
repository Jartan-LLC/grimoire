---
name: github-conventions
description: GitHub conventions -- branch naming, commit format, issue/PR templates, and safe issue/PR referencing in comments.
when_to_use: Using gh CLI, creating commits, posting PR/issue comments, or referencing issues by number.
user-invocable: false
---

# GitHub Conventions

CRITICAL: `#<number>` auto-links to issues/PRs on GitHub. Use `1.`/`2.`/`3.` for numbered lists and "Finding 1:"/"Item 1:" for labeled items -- never `#1`, `#2`, `#3` as markers.

Where the project's own rules say otherwise, follow them.

## Authentication

**Never reconfigure auth transport to unblock a command.** Don't switch the remote
between SSH and HTTPS, add a credential helper, or push to an explicit URL. A
missing key or token scope is a missing credential, not a transport problem --
only the user can supply it, and working around it changes config they never asked
you to touch, often globally. Stop and ask.

## Branches

Feature branches: `feature/<description>` or `feature/issue-<number>`
Always check if a branch already exists for an issue before creating a new one.

For sub-issues of a larger feature, branch from the parent feature branch rather than main. Sub-issue work merges back into the parent feature branch, which eventually merges to main.

## Commits

Follow the project's commit convention, as CONTRIBUTING, a commitlint config or the agent instructions state it, or as recent single-commit subjects on the default branch show it. Where none does, use Conventional Commits: `<type>(<scope>): <description>`, with a type from commitlint's config-conventional (`build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `refactor`, `revert`, `style`, `test`); the scope is optional.

Mark a change that breaks something for the project's consumers the way the convention and the project's release tool read it: `!` before the colon, a `BREAKING CHANGE:` footer, or both; where you cannot tell, both. A one-time action only contributors owe (rebuild the dev container) takes no breaking mark: state it in the first paragraph of the commit message and flag it in the PR description.

## Merge Setting

The merge setting decides which text becomes the commit on the default branch. Before writing a PR title or PR description, read [merge-setting.md](merge-setting.md): how to find the setting and what to write under each.

## Issues

Templates in `.github/ISSUE_TEMPLATE/` -- read them for section structure.

- **Bug reports**: must have label `bug`
- **Feature requests**: must have label `enhancement`

## Pull Requests

PR template at `.github/PULL_REQUEST_TEMPLATE.md` -- read it for section structure.
Use `Closes #<number>` to link PRs to issues.

## Code Reviews

Reviews are posted as PR comments. See [review-format.md](review-format.md) for the
recommended structure -- severity buckets and the `#N` footgun to avoid in the summary.

## Implementation Plans

Plans are posted as issue comments and saved to `.claude/workspace/`. See [plan-format.md](plan-format.md) for the recommended structure.
