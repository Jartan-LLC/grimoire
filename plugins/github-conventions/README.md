# GitHub Conventions

Branch naming, commit format, issue/PR templates, and safe issue/PR referencing in comments.

## Installation

```
/plugin marketplace add Jartan-LLC/grimoire
/plugin install github-conventions
```

## What's Included

### Skills

- **github-conventions** — branch naming (`feature/<desc>`), conventional commits (`feat:`, `fix:`, etc.), numbered list formatting (avoids `#N` auto-linking), plan format for implementation plans

### Hooks

- **PreToolUse** — automatically loads conventions when running GitHub write operations (`gh pr create`, `gh issue comment`, `git commit`, `git push`). Skips read-only commands (`gh pr view`, `gh pr list`, `git status`).

## License

MIT
