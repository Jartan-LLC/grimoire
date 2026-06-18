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
| [github-conventions](plugins/github-conventions/) | Branch naming, commit format, issue/PR templates |
| [memoria](plugins/memoria/) | Session memory and continuous learning — cross-session context, instinct-based pattern extraction |
| [praxis](plugins/praxis/) | Development workflow — issue planning, implementation, PR creation, code review |
| [recursio](plugins/recursio/) | Recursive multi-agent development with TDD — waves of parallel nested subagents |

## Contributing

New plugins go in `plugins/<name>/` with a `.claude-plugin/plugin.json` manifest. Add an entry to `.claude-plugin/marketplace.json` and submit a PR.

## License

MIT
