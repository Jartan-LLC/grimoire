# Contributing

## Setup

The dev container installs everything on creation. Elsewhere, install
[uv](https://docs.astral.sh/uv/), create a virtual environment with `uv venv`
(or activate one), then run:

```bash
make install
```

This installs the tools pinned in `ci/requirements.txt` and the pre-commit hook.
The lychee and actionlint hooks need Docker, and the markdownlint hook needs
Node. The tests need Node 20 or newer.

In the dev container, run the Docker hooks from inside the bind-mounted project
directory, or from a worktree under it. From a worktree or copy outside it, the
hooks cannot see the files and pass or fail wrongly.

## Before opening a PR

```bash
make check
```

`make fix` applies ruff's safe fixes and formatting, and `make help` lists every
target. CI runs more than `make check`: see `.github/workflows/ci.yml`.

## Tests

`make test` runs the Node and Python tests over git-tracked files, so `git add` a
new test first. To run one file:

```bash
node --test tests/<source path>/<name>.test.js       # node:test, Node 20 or newer
python3 -m pytest tests/<source path>/test_<name>.py # pytest, from ci/requirements.txt
```

- A function earns a test when it takes its input as an argument and a wrong
  answer from it would be silent.
- Every shipped hook entry point earns a process test: whatever arrives on
  stdin, it exits 0 and prints nothing or one well-formed JSON object.
- Tests live under `tests/`, mirroring the source path, never under `plugins/`.
- Build a fixture repository with `git init` in a temporary directory, never in
  this checkout. Fixtures write nothing outside their directory and reach no
  network.
- Keep a test that exposes a shipped defect. Wrap it in `knownDefect` from
  `tests/helpers/known-defect.js` (Node) or mark it
  `xfail(strict=True, raises=AssertionError)` (pytest), naming the issue. The fix
  removes the wrapper.

## Conventions

- Pure ASCII in every tracked file. `GUARDRAILS.md` has the substitution table.
- Commits follow [Conventional Commits](https://www.conventionalcommits.org/).
- We squash-merge with GitHub's default message, so every commit message on your
  branch lands on `main`, except merges from `main`. Write each for a later
  reader (`GUARDRAILS.md`).
- Any change under `plugins/<name>/` other than its `CHANGELOG.md` needs a
  `version` bump in that plugin's `plugin.json` and an entry for that version in
  its `CHANGELOG.md`. See [RELEASING.md](RELEASING.md).
- A change to the marketplace itself, such as adding or removing a plugin, gets
  an entry under `## Unreleased` in the root `CHANGELOG.md`.
- The Codex files are generated, so never hand-edit them:
  - `plugins/<name>/.codex-plugin/plugin.json`
  - `.agents/plugins/marketplace.json`
  - `plugins/<name>/codex/agents/*.toml`

  After you change a plugin's name, version, description, keywords, category or
  agents, run `python3 scripts/generate-codex.py` and commit its output. Until
  you do, `make verify` fails.

  `make verify` also names any orphaned file. Delete those yourself.
- Some hook scripts ship from more than one plugin (`DUPLICATED_HOOK_SCRIPTS` in
  `scripts/generate-codex.py`). Edit every copy in the same commit so they stay
  byte-identical; `make verify` fails while they differ. Bump each plugin that
  ships a copy.

  `find-duplicate-comments.js` reports the comments in these copies as retold;
  dismiss it.
- Report security issues privately via [SECURITY.md](.github/SECURITY.md).
- Ask questions in Discussions (Q&A). Report bugs and feature requests through
  the issue forms. Everyone taking part follows the
  [code of conduct](.github/CODE_OF_CONDUCT.md).

## Adding a plugin

1. Create `plugins/<name>/` with:
   - `.claude-plugin/plugin.json`, with `name`, `version`, `description` and
     `author`
   - a `README.md` saying what the plugin gives and how to install it
   - a `CHANGELOG.md` with an entry for that version
2. Add its entry to `.claude-plugin/marketplace.json` with the fields the other
   entries carry (`name`, `source`, `description`, `category`, `keywords`,
   `author`, `license`). Add its row to the plugin table in `README.md`.
3. If the plugin ships agents, copy `hooks/scripts/sync-codex-agents.js` from
   `plugins/recursio/` and add its `SessionStart` entry from
   `plugins/recursio/hooks/hooks.json`. Codex gets the agents only through that
   hook, and nothing checks that the hook is there.
4. Run `python3 scripts/generate-codex.py` and commit the output.
5. Add a line under `## Unreleased` in the root `CHANGELOG.md`.

## Maintaining

### Updating the lint hooks

Dependabot proposes weekly hook bumps, except for lychee. Bump lychee by hand:

```bash
pre-commit autoupdate --freeze --repo https://github.com/lycheeverse/lychee
```
