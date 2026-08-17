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
```

Both must pass -- CI runs the same checks. `make help` lists what each target
covers. `make test` joins them once the suite lands; see [Tests](#tests).

## Tests

This repository ships executable code -- the plugins' Node hook scripts and
reviewer tooling under `plugins/*/hooks/scripts/` and `plugins/*/skills/`, plus
`scripts/generate-codex.py`. `make lint` and `make verify` check ASCII, parsing,
linting and Codex drift; neither one calls a function. `make test` is the third
gate and the only one that does.

### What earns a test

One rule, both languages: **a function earns a test when it takes its input as
an argument and a wrong answer from it would be silent.** Silent is the
load-bearing half. A crash is found on the first run; a false clean is believed.
Every defect review has caught in this tooling had that shape -- an off-by-one in
diff line bookkeeping, a `--skip` value taken as a pattern so `--skip .*` would
report a clean tree, a CRLF-committed blob whose comments never matched, a
submodule gitlink that aborted the blob batch. Each was found by hand against a
throwaway repository. A test is that throwaway repository, kept.

Three classes:

1. **Pure logic behind a silent-wrong failure mode.** Required. This is the
   parsing, normalising, bookkeeping and gating code: the argument parser, skip
   matcher, comment index, diff walker and pair deduplicator in
   `find-duplicate-comments.js`; the token accounting and setting resolvers in
   `hooks/scripts/lib/transcript-context.js`; the sweep and session-id
   sanitising in `hooks/scripts/lib/session-state.js`; the cooldown split in
   `check-console-log.js`; the regex-flag and glob handling in
   `hooks/scripts/lib/utils.js`; and in `generate-codex.py` the frontmatter
   parser, the TOML string escaper, the role renderer and both drift finders.
2. **Process contracts.** Required, one per shipped hook entry point. A hook
   must exit 0 and emit either nothing or exactly one well-formed JSON object,
   whatever arrives on stdin. Spawn it with a hostile payload -- malformed JSON,
   empty input, a missing `transcript_path` -- and assert both. A hook that
   throws breaks the user's turn, and no other check here can see it.
3. **Everything else, deliberately untested.** The reasons are also the reasons
   not to grow the suite:
   - Thin wrappers over `fs` and `child_process` (`readFile`, `writeFile`,
     `runCommand`, `git`, `isGitRepo`, `commandExists`): the assertion would be
     that Node works.
   - Clock, environment and path accessors (`getDateString`, `getClaudeDir`,
     `getTempDir`): the assertion would restate the implementation.
   - Whether a hook's advice is good advice -- thresholds, wording, how often it
     repeats itself. That is a judgment call, not a fact, and freezing it in a
     test makes tuning it a test edit.

### Runners

One convention, two runners. What is worth sharing is the convention -- where
tests live, what earns one, explicit file lists, no dependencies. Each language
then uses its own standard library, and wrapping both in a common runner would
buy nothing.

| Aspect | Node | Python |
|---|---|---|
| Runner | `node:test` with `node:assert/strict` | `unittest` |
| Floor | Node 20 or newer | Python 3.12, as `verify` already uses |
| Location | `tests/<source path>/<name>.test.js` | `tests/<source path>/test_<name>.py` |
| Invocation | `node --test <file list>` | `python3 -m unittest <file list>` |

Nothing is installed to run the suite, and there is no `package.json` and no
`pyproject.toml` -- the same reason `.pre-commit-config.yaml` gives for leaving
ruff out. `pytest` is not used: it would earn its keep across a codebase, not
across one Python file.

**Tests live in `tests/`, not beside the code.** Two reasons, both specific to
this repository. Anything under `plugins/<name>/` is shipped to everyone who
installs that plugin, and a test suite is not part of the offer. And a content
change under `plugins/<name>/` requires a `version` bump in its `plugin.json`,
so co-located tests would force a release on every test edit for a plugin whose
shipped content did not change.

**Explicit file lists, not directory or glob discovery.** `node --test` reads
its path arguments differently across versions: a directory argument works on
Node 18 and fails on Node 24, a `**` glob works on Node 24 and fails on Node 18.
A list of files is the only form that works on both, which matters because a
contributor's Node and CI's Node are not the same. Python's `unittest discover`
wants an `__init__.py` in every test directory, since namespace-package
discovery was dropped; a path list wants none. So both halves of `make test`
build their list with `git ls-files` and hand it over.

**The file list must be non-empty.** `node --test` with no arguments walks the
whole tree rather than failing, and `git ls-files` exits 0 on no match, so an
unguarded list turns the gate into a silent pass. `make verify` already asserts
this for its JSON check; copy that assertion rather than reinventing it.

### Seams

A test reaches a function either by importing it or by spawning the script.
Importing needs a seam: `module.exports` naming the functions the suite uses,
plus a `require.main === module` guard so the CLI still runs. Modules under
`hooks/scripts/lib/` already export; extend the existing list.

Two rules keep seams honest:

- **A seam no test consumes is removed.** `find-duplicate-comments.js` shipped
  one ahead of its suite and it sat unused, which is an abstraction with no
  reader. Land a seam and its tests together.
- **Where require-time execution is the contract, spawn instead of importing.**
  `hooks.json` invokes `sync-codex-agents.js` as
  `require(root + '/hooks/scripts/sync-codex-agents.js')` and the script does its
  work at require time, so a `require.main` guard there would turn the hook into
  a no-op. Test it as a process, with `PLUGIN_ROOT` and `CODEX_HOME` pointed at
  temporary directories.

`scripts/generate-codex.py` cannot be imported by name -- the hyphen is not
valid in a module name. Load it with
`importlib.util.spec_from_file_location`.

### Fixtures

`find-duplicate-comments.js` and the git helpers need a repository, not a mock.
Build one: `git init` in a temporary directory, commit known contents, run
against it, delete it. Never against this checkout. The tool is written for
whichever repository is being reviewed, and a fixture that is this repository
lets a rule which suppresses a finding here look correct.

A fixture creates nothing outside its temporary directory and reaches no
network.

### Wiring

The Makefile owns every check, so `make test` is the single definition and CI
calls the target rather than restating the commands. Three edits, and the last
two are the ones to get right:

1. `Makefile` -- add `test` to the `.PHONY` line, and a `test:` target with a
   `##` help line and two recipe lines, Node then Python. Make stops at the
   first failing line, so a Node failure hides the Python result. That matches
   `verify`, which stops at its first failing sub-check, and is deliberate.
2. `.github/workflows/ci.yml` -- a new `test` job alongside `verify` and `lint`,
   pinning Node to 20 with `actions/setup-node` rather than taking the runner's
   default. The hook scripts run under whatever Node the user's harness carries,
   so the floor is the version worth testing on; a newer Node running code that
   passes on the floor is the safe direction. No version matrix: it doubles the
   hand-sync below to cover a risk the file-list rule already removes.
3. The `check` aggregator in the same file, in **both** places it names its
   dependencies -- the `needs:` list and the `results` array in its step. That
   file flags this as a footgun and it is: miss the array and the required
   status check goes green while the suite is red.

The target and its CI job land in the same change as the first tests, never
ahead of them. A gate wired up with nothing behind it reports success having
checked nothing, which is worse than no gate at all.

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
