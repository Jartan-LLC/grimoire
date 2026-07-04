# Grimoire

Curated Claude Code plugins for development workflows.

## Setup

```
/plugin marketplace add Jartan-LLC/grimoire
```

Then browse and install plugins:

```
/plugin
```

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
both `.claude-plugin/plugin.json` and its `.claude-plugin/marketplace.json` entry,
and is released with a `{plugin-name}--v{version}` git tag. Any content change needs
a version bump in both files, kept in lockstep.

See [RELEASING.md](RELEASING.md) for the full workflow and tag convention.

## Contributing

New plugins go in `plugins/<name>/` with a `.claude-plugin/plugin.json` manifest. Add an entry to `.claude-plugin/marketplace.json` and submit a PR.

## License

MIT
