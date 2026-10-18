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

Under Codex:

- It ignores plugin dependencies, so `praxis` needs `gitwise` installed
  explicitly.
- A Codex plugin cannot provide agents, so plugins that ship agents install
  them into your Codex config on session start instead.

## Available Plugins

| Plugin | Description |
|--------|-------------|
| [claudivis](plugins/claudivis/) | The key to Claude Code configuration -- how agents, skills, and commands work together |
| [gitwise](plugins/gitwise/) | GitHub conventions -- branch naming, commit format, issue/PR templates, and safe issue/PR referencing |
| [praxis](plugins/praxis/) | Development workflow -- issue planning, implementation, PR creation, code review with specialized reviewers, and project conventions |
| [pythonica](plugins/pythonica/) | Comprehensive Python development -- patterns, testing, async, error handling, packaging, configuration, type safety, resilience, observability, Pydantic, and more |
| [recursio](plugins/recursio/) | Recursive multi-agent development system with TDD -- decomposes projects into waves of parallel nested subagents |

## Versioning & Releases

Each plugin follows [semantic versioning](https://semver.org) and has its own
`CHANGELOG.md`. The root `CHANGELOG.md` lists the `marketplace-v*` releases you
can pin.

To update:

- In a Claude Code session, open `/plugin`, select grimoire on the Marketplaces
  tab and choose **Update marketplace**. Turn on auto-update there to update at
  each session start.
- In a shell, run `claude plugin update <plugin>@grimoire`.
- In Codex, run `codex plugin marketplace upgrade`.

To pin a project to a marketplace release, set `ref` to a
`marketplace-v<version>` tag in its `.claude/settings.json`:

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

In CI, `anthropics/claude-code-action`'s `plugin_marketplaces` input takes no
ref: check this repository out at the pinned tag and pass that local path.

## Contributing

To contribute, see [CONTRIBUTING.md](CONTRIBUTING.md). Report security issues
privately: [SECURITY.md](.github/SECURITY.md).

## License

MIT, except `plugins/praxis/skills/plain-writing/references/patterns.md`, which is
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/); see the
[praxis README](plugins/praxis/README.md#license).
