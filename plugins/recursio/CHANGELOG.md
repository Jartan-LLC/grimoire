# Changelog

## 2.0.0

- Breaking: the `recursive-development` skill is renamed `splitting-implementation` and rewritten around one decision: split a change across parallel subagents when it has several parts that are each real work, divide along file or module boundaries and can each be checked alone, or build it directly. When it splits, your agent settles shared interfaces, files and contract tests first, runs two to four parts per wave, briefs each part on its part alone, checks the combined code before the next wave, and tracks the split in `.claude/workspace/<effort>/split.md`. A part splits again at most once. TDD is no longer prescribed: test-first inside a part is allowed, not required.
- Breaking: the agents `recursive-orchestrator`, `recursive-planner`, `recursive-implementer` and `recursive-reviewer` are removed. Your agent spawns each part as a general-purpose subagent, or as a project or language agent that fits the part, and runs the split from the main thread.
- Breaking: the skills `recursive-planning`, `recursive-quality` and `recursive-execution` are removed. What still applies, such as the contract-richness guidance, is in `splitting-implementation`.
- Breaking: the `/recursio:recursive-implement` command is removed. Run `/recursio:splitting-implementation` with a plan file, an issue or a description instead: your agent builds it, splitting it where that pays.
- Breaking: recursio no longer ships Codex agent roles or the SessionStart hook that installed them. The installed roles stay until you delete them: remove `recursive-orchestrator.toml`, `recursive-planner.toml`, `recursive-implementer.toml` and `recursive-reviewer.toml` from `~/.codex/agents/grimoire/<version>/` (`$CODEX_HOME/agents/grimoire/<version>/` if you set `CODEX_HOME`), where `<version>` is the recursio version you upgraded from, such as `1.1.4`, and from any other version directory there that holds them.

## 1.1.4

- `recursive-implementer` writes comments only for what the code cannot say, docstrings where the language or the project asks for them, and no section dividers. It no longer adds a one-line comment to every public function.
- `recursive-planning` and `recursive-execution` create a CHANGELOG.md only for a new project. In a project that keeps one, they check the entry the work owes; they no longer add one to a project that keeps none.

## 1.1.3

- The README documents the SessionStart hook that installs the Codex agent roles.

## 1.1.2

- `recursive-implement` no longer sets `disable-model-invocation: true`, so an
  unprefixed `/recursive-implement` runs it and Claude can start it too.
