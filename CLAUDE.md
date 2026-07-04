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
- Keep `plugin.json` and `marketplace.json` versions in lockstep; bump on any content
  change under `plugins/<name>/` (see `RELEASING.md` for PATCH/MINOR/MAJOR)
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

There is no build system. Before declaring work done, confirm:

```bash
# Pure ASCII -- must print nothing
git grep -lP '[^\x00-\x7F]'

# JSON parses
python3 -c "import json,glob; [json.load(open(f)) for f in glob.glob('**/*.json', recursive=True)]"
```

Then confirm by inspection: each skill/agent frontmatter `name` matches its directory, and
any plugin with changed content under `plugins/<name>/` has a bumped `version` in both
`plugin.json` and its `marketplace.json` entry (kept in lockstep).
