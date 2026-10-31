# Pythonica

Comprehensive Python development -- patterns, testing, async, error handling, packaging, configuration, type safety, resilience, observability, Pydantic, and more.

## Installation

Claude Code:

```text
/plugin marketplace add Jartan-LLC/grimoire
/plugin install pythonica
```

Codex:

```bash
codex plugin marketplace add Jartan-LLC/grimoire
codex plugin add pythonica@grimoire
```

## Skills

### Core Language

- **python-patterns** -- protocols, context managers, concurrency, decorators, memory efficiency
- **python-type-safety** -- protocols, generics, type narrowing, mypy strict mode
- **async-python-patterns** -- asyncio fundamentals, when to use async vs sync, core patterns
- **python-resource-management** -- context managers (class + decorator), async resources, cleanup guarantees
- **python-anti-patterns** -- BAD->GOOD checklist for code review

### Testing

- **python-testing** -- pytest ecosystem: fixtures, parametrize, mocking, async testing, TDD workflow, coverage

### Error Handling & Resilience

- **python-error-handling** -- exception hierarchies, batch processing, validation patterns, Pydantic integration
- **python-resilience** -- retry with tenacity, exponential backoff, jitter, circuit breakers

### Project Setup

- **python-code-style** -- ruff/mypy config, docstrings, naming conventions
- **python-api-docs** -- Sphinx/autodoc/napoleon/MyST, doctest, intersphinx, strict docs CI gate
- **python-project-structure** -- directory layout, `__all__`, flat vs nested
- **python-packaging** -- pyproject.toml, src layout, build backends, entry points
- **python-configuration** -- pydantic-settings, env vars, 12-factor methodology
- **uv-package-manager** -- uv workflows, migration from pip/poetry, Docker/CI patterns

### Operations

- **python-observability** -- structlog, correlation IDs, semantic log levels
- **python-performance-optimization** -- profiling, optimization checklist

### Frameworks

- **pydantic** -- v2 API, validators, serialization, settings, FastAPI/SQLAlchemy/Django integration

## Credits

- [wshobson/agents](https://github.com/wshobson/agents) by Seth Hobson -- `async-python-patterns`, `python-anti-patterns` except its language-level anti-patterns, `python-code-style`, `python-configuration`, `python-error-handling`, `python-observability`, `python-packaging`, `python-performance-optimization`, `python-project-structure`, `python-resilience`, `python-resource-management`, `python-type-safety`, `uv-package-manager` and `python-testing`'s `references/` (MIT; `LICENSE-wshobson-agents` in each skill's directory)
- [everything-claude-code](https://github.com/affaan-m/everything-claude-code) by Affaan Mustafa -- `python-patterns`, `python-testing`'s SKILL.md and `python-anti-patterns`' language-level anti-patterns (MIT; `LICENSE-everything-claude-code` in each skill's directory)
- [claude-mpm-skills](https://github.com/bobmatnyc/claude-mpm-skills) by Claude MPM Contributors -- `pydantic` (MIT; `LICENSE-claude-mpm-skills` in the skill's directory)

## License

MIT
