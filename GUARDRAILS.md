# Project Guardrails

The project rules, ranked by how firmly each holds. `CLAUDE.md` imports this file, so
every Claude Code session loads it; Liza agents also enforce the tiers (Liza's `CORE.md`).

## Tier 0 (Inviolable)
<!-- Constraints that must NEVER be violated. Triggers mandatory halt (RESET). -->

- Never put secrets or credentials in tracked files.

## Tier 1 (Hard Constraints)
<!-- Suspended only with explicit waiver. -->

- **Pure ASCII in every tracked file.** No em-dashes, smart quotes, arrows,
  box-drawing, accented letters, or other non-ASCII. Use the ASCII equivalents:
  `--` (em-dash), `->` / `<-` / `<->` (arrows), `>=` `<=` `!=` (comparators),
  `x` (times), `^2` (superscript), `...` (ellipsis), plain `'` and `"` (quotes),
  and `|` `` ` `` `-` for directory trees. Applies to prose, code fences, JSON
  descriptions, and hook scripts alike.
- Run the Verify command in `CLAUDE.md` before declaring work done or submitting it for
  review.
- Version lives only in `plugin.json`; bump it on any content change under
  `plugins/<name>/` (marketplace entries carry no `version` -- see `RELEASING.md`).
- Declare a plugin `dependency` for every cross-plugin skill an agent loads in its
  frontmatter `skills:` (a hard, resolve-or-fail load like `gitwise:github-conventions`);
  a prose `see plugin:skill` pointer is soft and needs none. Add no plugin `dependency`
  without a real runtime requirement (see `RELEASING.md`).
- Ask first before changing a plugin's public surface (command, agent or skill names) or
  a skill's severity mapping, deleting files, or removing a plugin or feature.
- Commit or push only when explicitly asked or instructed by a command. A Liza workflow
  step that commits counts as that instruction; none counts for pushing or opening pull
  requests, which stay human-initiated.
- State the reason for every dependency you add.

## Tier 2 (Strong Defaults)
<!-- Best-effort under pressure. -->

- Read `README.md` and `RELEASING.md` before changing plugin structure or versioning.
- Update the affected READMEs and skills alongside any change.
- Executable code earns tests by one rule -- pure input, silent-wrong output -- and hook
  entry points earn a process contract; `CONTRIBUTING.md` holds the rule, the runners,
  the layout and the CI wiring.
- Reviewer agents tier findings with the `review-severity` skill; agents name their lens
  and reference skills (agents = role, skills = knowledge; see `claudivis:claude-config`).
- Don't restate a referenced skill's rules or examples inside an agent or command --
  point to the skill.
- Write Google-style docstrings for public modules, classes, and functions in the Python
  code (enforced by ruff `D`) and full type annotations (enforced by pyright `strict`).
- Write plans to `.claude/workspace/` in the project root for non-trivial changes.
- Don't wrap things the underlying library already expresses clearly.
- Don't speculate about fixes -- investigate first, then propose.
- Don't hardcode derived counts in prose or comments -- they drift silently.
- Comments state only the load-bearing why. Rationale goes in the commit message; a PR
  body carries only the gotchas.

## Tier 3 (Preferences)
<!-- Degraded gracefully. -->

---

<!-- Liza agents recite this word to prove they read the file (see Liza's CORE.md). Keep it. -->
Secret word: On-rails
