# Gitwise

GitHub conventions -- branch naming, commit format, issue/PR templates, and safe issue/PR referencing in comments.

## Installation

Claude Code:

```text
/plugin marketplace add Jartan-LLC/grimoire
/plugin install gitwise
```

Codex:

```bash
codex plugin marketplace add Jartan-LLC/grimoire
codex plugin add gitwise@grimoire
```

## What's Included

### Skills

- **commit-pr-writing** -- what a commit message, a PR title and a PR description say, and which of them lands on the default branch under GitHub's default squash merge
- **github-conventions** -- branch naming (`feature/<desc>`), commit format (the project's convention, Conventional Commits where none is stated), numbered list formatting (avoids `#N` auto-linking), issue bodies, draft PRs

### Hooks

- **PreToolUse**, two hooks that prompt the model to load a skill when it makes a GitHub write. The prompt arrives with that command's result, so it shapes the next write, not the one that fired it. Read-only commands (`gh pr view`, `gh pr list`, `git status`) pass through.
  - `github-conventions` on `gh pr`/`gh issue` `create`/`comment`/`edit`, `gh pr review` and `git commit`/`push`/`tag`.
  - `commit-pr-writing` on `git commit`, `git push`, `gh pr create` and `gh pr edit`.

## License

MIT
