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
| [github-conventions](plugins/github-conventions/) | GitHub conventions — branch naming, commit format, issue/PR templates, and safe issue/PR referencing |
| [memoria](plugins/memoria/) | Session memory and continuous learning — cross-session context, pattern extraction, instinct-based learning |
| [praxis](plugins/praxis/) | Development workflow — issue planning, implementation, PR creation, code review with specialized reviewers, and project conventions |
| [pythonica](plugins/pythonica/) | Comprehensive Python development — patterns, testing, async, error handling, packaging, configuration, type safety, resilience, observability, Pydantic, and more |
| [recursio](plugins/recursio/) | Recursive multi-agent development system with TDD — decomposes projects into waves of parallel nested subagents |

## Contributing

New plugins go in `plugins/<name>/` with a `.claude-plugin/plugin.json` manifest. Add an entry to `.claude-plugin/marketplace.json` and submit a PR.

## License

MIT
