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
make lint     # every file-level linter, via pre-commit
make verify   # ASCII, JSON parses, Codex generated-file drift
```

Both must pass. CI runs the same two commands and nothing else.

## Conventions

- Pure ASCII in every tracked file. See `CLAUDE.md` for the substitution table.
- Commits follow [Conventional Commits](https://www.conventionalcommits.org/)
  (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`).
- Any content change under `plugins/<name>/` needs a `version` bump in that
  plugin's `plugin.json`. See [RELEASING.md](RELEASING.md) for the bump rule and
  the tag convention.
- Never hand-edit the generated Codex files. Run `python3 scripts/generate-codex.py`
  and commit its output.

## Updating the lint hooks

Hook revisions are pinned to commit SHAs with a `# frozen: vX.Y.Z` comment.
Bump them all with:

```bash
pre-commit autoupdate --freeze
```
