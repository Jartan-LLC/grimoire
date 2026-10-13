# Contributing

## Setup

The dev container installs everything on create. Elsewhere, install
[uv](https://docs.astral.sh/uv/), create a virtual environment with `uv venv`
(or activate one), then run:

```bash
make install
```

It installs the tools pinned in `ci/requirements.txt` and the pre-commit hook.
The hooks also need Docker (lychee, actionlint) and Node (markdownlint). Run the
Docker hooks from the bind-mounted project directory: from a worktree or a copy
they report missing files.

## Before opening a PR

```bash
make check
```

`make fix` applies ruff's safe fixes and formatting. `make help` lists every
target.

## Tests

`make test` runs both suites over git-tracked files, so `git add` a new test
first. To run one file:

```bash
node --test tests/<source path>/<name>.test.js      # node:test, Node 20 or newer
python3 -m pytest tests/<source path>/test_<name>.py # pytest, from ci/requirements.txt
```

- A function earns a test when it takes its input as an argument and a wrong
  answer from it would be silent.
- Every shipped hook entry point earns a process test: whatever arrives on stdin,
  it exits 0 and prints nothing or one well-formed JSON object.
- Tests live under `tests/`, mirroring the source path, never under `plugins/`.
- A fixture repository is built with `git init` in a temporary directory, never
  this checkout. Fixtures write nothing outside their directory and reach no
  network.

## Conventions

- Pure ASCII in every tracked file. See `GUARDRAILS.md` for the substitution table.
- Commits follow [Conventional Commits](https://www.conventionalcommits.org/).
- Any change under `plugins/<name>/` other than its `CHANGELOG.md` needs a
  `version` bump in that plugin's `plugin.json` and an entry for that version in
  its `CHANGELOG.md`. See [RELEASING.md](RELEASING.md).
- A change to the marketplace itself, such as a plugin added or removed, gets an
  entry under `## Unreleased` in the root `CHANGELOG.md`.
- Never hand-edit the generated Codex files. Run `python3 scripts/generate-codex.py`
  and commit its output.
- Report security issues privately via [SECURITY.md](.github/SECURITY.md).

## Updating the lint hooks

Dependabot proposes hook bumps weekly, except lychee's. Bump that one by hand:

```bash
pre-commit autoupdate --freeze --repo https://github.com/lycheeverse/lychee
```
