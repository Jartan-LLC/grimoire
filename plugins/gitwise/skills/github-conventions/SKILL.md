---
name: github-conventions
description: GitHub conventions -- branch naming, commit format, issue/PR templates, and safe issue/PR referencing in comments.
when_to_use: Using gh CLI, creating commits, posting PR/issue comments, or referencing issues by number.
user-invocable: false
---

# GitHub Conventions

CRITICAL: `#<number>` auto-links to issues/PRs on GitHub. Use `1.`/`2.`/`3.` for numbered lists and "Finding 1:"/"Item 1:" for labeled items -- never `#1`, `#2`, `#3` as markers.

## Authentication

**Never reconfigure a repository's auth transport to get a command working.** If
the remote is SSH and the key is missing, or the token lacks a scope, stop and
ask for it to be fixed. Do not switch the remote to HTTPS, add a credential
helper, or route around it with an explicit URL.

A blocked push is a missing credential, not a transport problem. Working around
it hides the real cause, silently changes config the user did not ask you to
touch -- often globally, affecting every other repository -- and leaves the
project on a transport nobody chose. The user is the only one who can add a key
or grant a scope, so surface it and wait.

## Branches

Feature branches: `feature/<description>` or `feature/issue-<number>`
Always check if a branch already exists for an issue before creating a new one.

For sub-issues of a larger feature, branch from the parent feature branch rather than main. Sub-issue work merges back into the parent feature branch, which eventually merges to main.

## Commits

Conventional commits format: `<type>: description`

Types: `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`
Optional scope: `feat(frontend): description`

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
