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

- **commit-pr-writing** -- what a commit message, a PR title and a PR description say, and which of them lands on the default branch under the repository's merge setting
- **github-conventions** -- branch naming (`feature/<desc>`), commit format (the project's convention, Conventional Commits where none is stated), numbered list formatting (avoids `#N` auto-linking), plan format for implementation plans

### Hooks

- **PreToolUse** -- prompts the model to load the skills when it makes a GitHub write (the prompt arrives with that command's result, so it shapes the next write, not the one that fired it): `commit-pr-writing` and `github-conventions` before `git commit`, `git push`, `gh pr create` and `gh pr edit`; `github-conventions` alone before `gh issue` `create`/`comment`/`edit`, `gh pr comment`, `gh pr review` and `git tag`. Read-only commands (`gh pr view`, `gh pr list`, `git status`) pass through.

## License

MIT
