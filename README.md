# Grimoire

[![CI](https://github.com/Jartan-LLC/grimoire/actions/workflows/ci.yml/badge.svg)](https://github.com/Jartan-LLC/grimoire/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/Jartan-LLC/grimoire/badge)](https://scorecard.dev/viewer/?uri=github.com/Jartan-LLC/grimoire)

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

Each plugin follows [semantic versioning](https://semver.org), and each version
gets a `{plugin-name}--v{version}` git tag. Each plugin has its own
`CHANGELOG.md`, and the root `CHANGELOG.md` covers marketplace releases.

To update, run `/plugin marketplace update grimoire` in a Claude Code session
(or `claude plugin update <plugin>@grimoire` in a shell), or
`codex plugin marketplace upgrade` in Codex. To pin a project to a marketplace
release, set `ref` to a `marketplace-v<version>` tag in its
`.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "grimoire": {
      "source": { "source": "github", "repo": "Jartan-LLC/grimoire", "ref": "marketplace-v1.0.0" }
    }
  }
}
```

A pinned project gets newer plugin versions only when you move `ref` to a newer
`marketplace-v*` tag.

In CI, check this repository out at the pinned tag and pass the local path
to `anthropics/claude-code-action`'s `plugin_marketplaces` input, which takes
no ref.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) to set up, check a change or add a
plugin, and [RELEASING.md](RELEASING.md) to cut a release. Report security
issues privately: [SECURITY.md](.github/SECURITY.md).

## License

MIT
