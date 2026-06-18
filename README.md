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
| [recursion](plugins/recursion/) | Recursive multi-agent development with TDD — waves of parallel nested subagents |

## Contributing

Create a new directory at the repo root with your plugin name. Include:

```
your-plugin/
  .claude-plugin/plugin.json
  skills/
  agents/
  commands/
  README.md
```

Add an entry to `.claude-plugin/marketplace.json` and submit a PR.

## License

MIT
