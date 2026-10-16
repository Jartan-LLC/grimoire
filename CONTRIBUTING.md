# Contributing

## Setup

The dev container installs everything on create. Elsewhere, install
[uv](https://docs.astral.sh/uv/), create a virtual environment with `uv venv`
(or activate one), then run:

```bash
make install
```

It installs the tools pinned in `ci/requirements.txt` and the pre-commit hook.
The hooks also need Docker (lychee, actionlint) and Node (markdownlint), and the
tests need Node 20 or newer. Run the Docker hooks from inside the bind-mounted
project directory (a worktree under it works): from a worktree or a copy
elsewhere they cannot see the files and pass or fail wrongly.

## Before opening a PR

```bash
make check
```

`make fix` applies ruff's safe fixes and formatting. `make help` lists every
target. CI runs more than this: see `.github/workflows/ci.yml`.

## Tests

`make test` runs the Node and Python tests over git-tracked files, so `git add` a
new test first. To run one file:

```bash
node --test tests/<source path>/<name>.test.js       # node:test, Node 20 or newer
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
- A test that exposes a shipped defect stays, wrapped in `knownDefect` from
  `tests/helpers/known-defect.js` (Node) or marked
  `xfail(strict=True, raises=AssertionError)` (pytest), naming the issue. The fix
  removes the wrapper.

## Conventions

- Pure ASCII in every tracked file. See `GUARDRAILS.md` for the substitution table.
- Commits follow [Conventional Commits](https://www.conventionalcommits.org/).
- We squash-merge with GitHub's default message, so every commit message on your
  branch (merges from `main` aside) lands on `main`: write each for a later reader
  (`GUARDRAILS.md`).
- Any change under `plugins/<name>/` other than its `CHANGELOG.md` needs a
  `version` bump in that plugin's `plugin.json` and an entry for that version in
  its `CHANGELOG.md`. See [RELEASING.md](RELEASING.md).
- A change to the marketplace itself, such as a plugin added or removed, gets an
  entry under `## Unreleased` in the root `CHANGELOG.md`.
- The Codex files are generated: `plugins/<name>/.codex-plugin/plugin.json`,
  `.agents/plugins/marketplace.json` and `plugins/<name>/codex/agents/*.toml`.
  Never hand-edit them. After a change to a plugin's name, version, description,
  keywords, category or agents, run `python3 scripts/generate-codex.py` and commit
  its output; `make verify` fails until you do, and names any orphaned file for
  you to delete.
- A hook script that ships from more than one plugin (`DUPLICATED_HOOK_SCRIPTS`
  in `scripts/generate-codex.py`) must stay byte-identical: edit every copy in the
  same commit (`make verify` fails while they differ), and bump each plugin that
  ships one. `find-duplicate-comments.js` reports the comments in these copies as
  retold; dismiss it.
- Report security issues privately via [SECURITY.md](.github/SECURITY.md).
- Ask questions in Discussions (Q&A) and report bugs and feature requests through
  the issue forms; everyone taking part follows the
  [code of conduct](.github/CODE_OF_CONDUCT.md).

## Adding a plugin

1. Create `plugins/<name>/` with `.claude-plugin/plugin.json` (`name`,
   `version`, `description`, `author`), a `README.md` saying what the plugin
   gives and how to install it, and a `CHANGELOG.md` with an entry for that
   version.
2. Add its entry to `.claude-plugin/marketplace.json` with the fields the other
   entries carry (`name`, `source`, `description`, `category`, `keywords`,
   `author`, `license`), and its row to the plugin table in `README.md`.
3. If the plugin ships agents, copy `hooks/scripts/sync-codex-agents.js` from
   `plugins/recursio/` and add its `SessionStart` entry from
   `plugins/recursio/hooks/hooks.json`: Codex gets the agents only through that
   hook, and nothing checks that it is there.
4. Run `python3 scripts/generate-codex.py` and commit the output.
5. Add a line under `## Unreleased` in the root `CHANGELOG.md`.

## Maintaining

### Updating the lint hooks

Dependabot proposes hook bumps weekly, except lychee's. Bump that one by hand:

```bash
pre-commit autoupdate --freeze --repo https://github.com/lycheeverse/lychee
```
