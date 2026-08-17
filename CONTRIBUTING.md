# Contributing

## Setup

Grimoire has no build step. The only local tooling is
[pre-commit](https://pre-commit.com/), which the devcontainer wires up for you
on create:

```bash
make install
```

That installs pre-commit and registers the git hook, so the linters run on every
commit. Some hooks need Docker (lychee, actionlint) and Node (markdownlint); the
devcontainer has both. The Docker hooks resolve the workspace by inspecting the
container, so run them from the bind-mounted project directory -- from a
worktree or a copy elsewhere they report missing files rather than a mount
error.

## Before opening a PR

```bash
make lint
make verify
make test
```

Both must pass -- CI runs the same checks. `make help` lists what each target
covers.

## Conventions

- Pure ASCII in every tracked file. See `CLAUDE.md` for the substitution table.
- Commits follow [Conventional Commits](https://www.conventionalcommits.org/)
  (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`).
- Any content change under `plugins/<name>/` needs a `version` bump in that
  plugin's `plugin.json`. See [RELEASING.md](RELEASING.md) for the bump rule and
  the tag convention.
- Never hand-edit the generated Codex files. Run `python3 scripts/generate-codex.py`
  and commit its output.
- Report security issues privately via [SECURITY.md](.github/SECURITY.md), not a
  public issue.

## Updating the lint hooks

Dependabot's `pre-commit` ecosystem proposes hook bumps weekly. It cannot see
the lychee hook: lychee tags are prefixed (`lychee-v0.24.2`), so Dependabot
cannot parse a version out of the `# frozen:` comment and reports the hook as
permanently up to date. Bump that one by hand:

```bash
pre-commit autoupdate --freeze --repo https://github.com/lycheeverse/lychee
```

Everything else is covered by the weekly group, or by a bare
`pre-commit autoupdate --freeze` to bump them all.
