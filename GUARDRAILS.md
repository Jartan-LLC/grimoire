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
- Version lives only in `plugin.json`; bump it on any change under `plugins/<name>/`
  other than its `CHANGELOG.md`, with an entry for the new version in that changelog
  (marketplace entries carry no `version` -- see `RELEASING.md`).
- Declare a plugin `dependency` for every cross-plugin skill an agent loads in its
  frontmatter `skills:` or a skill or command step loads (a hard, resolve-or-fail load like
  `gitwise:github-conventions`). Add
  no plugin `dependency` without a real runtime requirement (see `RELEASING.md`).
- Name no other plugin, and no skill, agent or command of another plugin, in a skill, agent or
  command unless its plugin declares that plugin. Drop a prose pointer to an undeclared plugin
  rather than add a dependency for it; a `skills:` load or a step that loads another plugin's
  skill is a runtime requirement and takes the dependency above.
- Ask first before changing a plugin's public surface (command, agent or skill names) or
  a skill's severity mapping, deleting files, or removing a plugin or feature.
- Commit or push only when explicitly asked or instructed by a command. A Liza workflow
  step that commits counts as that instruction; none counts for pushing or opening pull
  requests, which stay human-initiated.
- State the reason for every dependency you add in the commit message that adds it.

## Tier 2 (Strong Defaults)
<!-- Best-effort under pressure. -->

- Read `CONTRIBUTING.md` before adding or restructuring a plugin, and `RELEASING.md`
  before changing versions or dependencies.
- Update, in the same change, every README, doc, skill and agent file the change makes
  false: search them for each name, flag, path and default the diff changes.
- Run the Docker pre-commit hooks (lychee, actionlint), and so `make lint` and
  `make check`, from inside the bind-mounted checkout (worktrees under it work): from a
  worktree or copy outside it they cannot see the files and pass or fail wrongly (see
  `CONTRIBUTING.md`).
- Executable code earns tests by one rule -- pure input, silent-wrong output -- and hook
  entry points earn a process contract; `CONTRIBUTING.md` holds the rule and the layout.
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
- Comments state only the load-bearing why; a change's reason goes in its commit message.
- Grimoire squash-merges PRs with GitHub's default commit message, unedited, so every
  commit message on a branch, merges from `main` aside, lands on `main`. Before writing a commit message, a PR title
  or a PR description, read `plugins/gitwise/skills/commit-pr-writing/SKILL.md` (the
  `gitwise:commit-pr-writing` skill); a commit message never lists files or narrates
  review rounds.

## Tier 3 (Preferences)
<!-- Degraded gracefully. -->

---

<!-- Liza agents recite this word to prove they read the file (see Liza's CORE.md). Keep it. -->
Secret word: On-rails
