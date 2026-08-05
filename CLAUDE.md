# Grimoire

A Claude Code plugin marketplace. Each plugin lives in `plugins/<name>/` with a
`.claude-plugin/plugin.json` manifest and a mirrored entry in
`.claude-plugin/marketplace.json`.

## Rules

### Always

- **Pure ASCII in every tracked file.** No em-dashes, smart quotes, arrows,
  box-drawing, accented letters, or other non-ASCII. Use the ASCII equivalents:
  `--` (em-dash), `->` / `<-` / `<->` (arrows), `>=` `<=` `!=` (comparators),
  `x` (times), `^2` (superscript), `...` (ellipsis), plain `'` and `"` (quotes),
  and `|` `` ` `` `-` for directory trees. Applies to prose, code fences, JSON
  descriptions, and hook scripts alike.
- Read `README.md` and `RELEASING.md` before changing plugin structure or versioning
- Version lives only in `plugin.json`; bump it on any content change under
  `plugins/<name>/` (marketplace entries carry no `version` -- see `RELEASING.md`)
- Declare a plugin `dependency` for every cross-plugin skill an agent loads in its
  frontmatter `skills:` (a hard, resolve-or-fail load like `gitwise:github-conventions`);
  a prose `see plugin:skill` pointer is soft and needs none
- Update the affected READMEs and skills alongside any change
- Reviewer agents tier findings with the `review-severity` skill; agents name their
  lens and reference skills -- they do not restate a skill's rules (agents = role,
  skills = knowledge; see `claudivis:claude-config`)

### Anti-patterns

- Don't restate a referenced skill's rules or examples inside an agent or command --
  point to the skill
- Don't speculate about a fix -- investigate first, then propose
- Don't hardcode derived counts in prose -- they drift silently

### Ask first

- Changing a plugin's public surface (command/agent/skill names) or a skill's
  severity mapping
- Deleting files or removing a plugin or feature

### Never

- Commit or push unless explicitly asked or instructed by a command
- Add a plugin `dependency` without a real runtime requirement (see `RELEASING.md`)
- Put secrets or credentials in tracked files
- Introduce non-ASCII characters (see the ASCII rule above)

## Corrections

## Skills

## Verify

The Makefile owns every check, so they live in one place. Before declaring work
done, confirm:

```bash
make verify   # pure ASCII, every tracked JSON parses, Codex files match sources
make lint     # every file-level linter, via pre-commit
```

CI runs the same checks. `AGENTS.md` is a symlink to this file, not a second
source of truth -- edit `CLAUDE.md`.

Then confirm by inspection: each skill/agent frontmatter `name` matches its directory, and
any plugin with changed content under `plugins/<name>/` has a bumped `version` in
`plugin.json`.
