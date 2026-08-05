# Grimoire

Curated plugins for development workflows, for Claude Code and Codex.

## Setup

Claude Code:

```text
/plugin marketplace add Jartan-LLC/grimoire
```

Then browse and install plugins:

```text
/plugin
```

Codex:

```bash
codex plugin marketplace add Jartan-LLC/grimoire
codex plugin add <plugin>@grimoire
```

Skills and hooks behave the same under both. Two things differ: Codex ignores
plugin dependencies, so `praxis` needs `gitwise` installed explicitly, and it has
no plugin-level agent surface, so plugins shipping agents install them into your
Codex config on session start instead.

## Available Plugins

| Plugin | Description |
|--------|-------------|
| [claudivis](plugins/claudivis/) | The key to Claude Code configuration -- how agents, skills, and commands work together |
| [gitwise](plugins/gitwise/) | GitHub conventions -- branch naming, commit format, issue/PR templates, and safe issue/PR referencing |
| [praxis](plugins/praxis/) | Development workflow -- issue planning, implementation, PR creation, code review with specialized reviewers, and project conventions |
| [pythonica](plugins/pythonica/) | Comprehensive Python development -- patterns, testing, async, error handling, packaging, configuration, type safety, resilience, observability, Pydantic, and more |
| [recursio](plugins/recursio/) | Recursive multi-agent development system with TDD -- decomposes projects into waves of parallel nested subagents |

## Versioning & Releases

Each plugin uses [semantic versioning](https://semver.org), with its version in
`.claude-plugin/plugin.json` (the marketplace entry carries none -- Claude Code
resolves the manifest first), and is released with a `{plugin-name}--v{version}`
git tag. Any content change needs a version bump.

See [RELEASING.md](RELEASING.md) for the full workflow and tag convention.

## Contributing

New plugins go in `plugins/<name>/` with a `.claude-plugin/plugin.json` manifest.
Add an entry to `.claude-plugin/marketplace.json` and submit a PR.

Local checks, run by CI and by the pre-commit hook:

```bash
make lint     # every file-level linter, via pre-commit
make verify   # ASCII, JSON parses, Codex generated-file drift
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and conventions.

## License

MIT
