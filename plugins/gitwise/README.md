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

- **github-conventions** -- branch naming (`feature/<desc>`), commit format (the project's convention, Conventional Commits where none is stated), how the merge setting decides which text lands on the default branch, numbered list formatting (avoids `#N` auto-linking), plan format for implementation plans

### Hooks

- **PreToolUse** -- prompts the model to load the conventions before a GitHub write: `gh pr` or `gh issue` `create`/`comment`/`edit`, `gh pr review`, `git commit`, `git push` and `git tag`. Read-only commands (`gh pr view`, `gh pr list`, `git status`) pass through.

## License

MIT
