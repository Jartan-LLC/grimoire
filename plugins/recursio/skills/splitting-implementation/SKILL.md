---
name: splitting-implementation
description: Deciding whether to split an implementation across parallel subagents, and splitting it so the parts fit together. Most changes are best built directly; a large change that divides along loosely coupled files or modules is split into small waves, with shared interfaces, files and contract tests settled first, each subagent briefed on its part alone, and the combined code verified before the next wave.
when_to_use: Before spawning subagents to write code, or when about to implement a feature, issue or project with several parts (for example 'build X with A, B and C', several new modules, a multi-part feature); also when given one part of such a split to build. Not for one-file fixes, splitting work into issues or PRs, splitting one file into modules, or recursive algorithms.
user-invocable: false
---

# Splitting Implementation

Whether to divide implementation work among subagents in one session, and how to divide it so the parts fit together. The main thread is the root of every split. A level is any agent that splits its work: the main thread, or a part that splits again.

## 1. Split or build

A part whose brief says it is two levels below the main thread is at the depth limit: it builds its part and never splits, whatever else this skill says. [Parts that load this skill on their own re-split past the limit and collide.]

Otherwise, build it yourself unless all three hold:

- **Large**: more than one context holds comfortably, or several modules.
- **Loosely coupled**: it divides along file or module boundaries. Tightly or circularly coupled files, and a feature with its tests, stay in one part. [Each side of a tight coupling guesses at the other.]
- **Checkable in parts**: each part can be checked alone, by something short of the whole system. [A part that cannot be checked alone fails only at the barrier, after its context is gone.]

Do not split a sequential chain where each step needs the last, one monolithic failing check, a quick targeted change, or parts that would each be one function or one test file. Splitting buys accuracy and context relief, not speed: it costs several times the tokens and usually more wall clock.

A wide, same-shaped edit across many files, such as a rename or a mechanical migration, fits Claude Code's built-in `/batch`: suggest it to the user rather than splitting.

A level that cannot spawn subagents (no Agent tool, or running under Codex) builds its parts itself, wave by wave, still settling first (section 4).

This skill covers dividing work among subagents in one session. Dividing work into issues or PRs is a separate decision.

## 2. Standing rules

If this skill was lost to compaction, load it again and resume from the status lines in split.md.

- Scopes are disjoint: every file belongs to one part. [Parts share one workspace with no lock; two writers lose work.]
- Contract files and contract tests are read-only to parts. [A part that edits them passes its own tests and breaks a sibling.]
- No agent below the main thread stages, commits, pushes or switches branches, and the main thread never commits while a wave runs. Stage files by name, never `git add -A`. [A commit mid-wave captures a sibling's half-written files.]
- Parts run formatters and installers on their own scope only. [A repo-wide run rewrites a sibling's files under it.]
- Never hand a brief down unsplit: split it into two or more parts, or build it. [A pass-through level adds tokens and no relief.]
- A part asks no questions; it reports. [A question ends the part with nothing built.]
- Parts that only build do not need this skill, so each brief carries the rules its part needs (section 7).

## 3. Splitting again

A part splits again only when both hold: after reading its slice it finds sub-structure its parent could not have listed, and holding the whole slice would overload its context. If the parent could have seen the split, the parent splits flat into a later wave instead. [Each extra level adds briefs and a barrier that a flat split does without.]

A part whose slice is too big and does not split cleanly reports up rather than building it in one pass. [Building it in one pass overloads the part's context.]

The ceiling: a part one level below the main thread may split once. Its parts are two levels below and build. A part that meets the gate but has no Agent tool builds its part and reports "could not split". [A silent fallback reads as success.]

## 4. Settle before splitting

List the decisions that two or more parts would each make and that must agree, in this order:

1. Interfaces and shared types.
2. Hub files and shared manifests: export lists, package files, `__init__.py`.
3. New dependencies.
4. File and test layout.

Then, as judgement, settle what parts could otherwise do differently: naming, error shape, logging, docstring style. The project's own rules already reach every subagent through CLAUDE.md.

Take each answer from the project first, then from what the parent or the plan passed down; otherwise decide it and record it in split.md. A decision only one part makes stays with that part. Settle interfaces and decisions; never dictate implementation or hand down code snippets. [A parent that writes a part's internals spends its own context and loses the part's judgement.]

## 5. Contracts and contract tests

Before the wave, the level writes the shared types, interfaces and hub files itself, and writes or names, from the contract, the tests that define each part's interface. Both are read-only to parts. Inside a part, test-first is allowed, not required. [Parts pass alone and fail together when only their own tests define the interface.]

A contract sets the ceiling for the code built on it:

- **Completeness**: enumerate all operations, not just common ones; enums for closed sets (prevents string-typing drift); error types alongside success types (`Record | ParseError`); a custom exception hierarchy, base plus subtypes per failure domain.
- **Flexibility**: batch interfaces (`list[Spec]`) over single-item; injectable I/O (write callables, output streams) for testability; union return types for expected failures, exceptions for unexpected ones.
- **Modularity**: protocols or interfaces for dependency injection, not concrete dependencies; factories or registries for runtime selection; structured return types (`RunResult`) over bare values.
- **Typing boundaries**: untyped values (`Any`, `object`) only at input boundaries, such as parsed records, CLI arguments and external data whose shape is unknown; every internal result type fully typed, since its shape is known at design time. A contracts file holds protocols, dataclasses, enums, type aliases and constants, and no callable stubs.

## 6. Plan the waves

- Two to four parts per wave; more parts go to later waves, not a wider wave. [Wider waves collide and drift more.]
- A part that consumes another part's interface goes in a later wave, so it builds against real code. Run it in parallel against a declared contract only when the contract is small and stable.
- Parts that need the same file go in different waves, unless it is a hub file the level writes itself. [The workspace has no lock.]
- Before each wave, check that the parts' scopes together cover every file the task touches, with hub and shared files owned by the level. [An unowned file is written by no part, or by two.]
- When the root cannot see how an area splits, it first sends a read-only Explore subagent to map the area, then splits flat.
- Record the waves, parts and scopes in split.md (section 11).

## 7. Briefs

A brief carries everything its part needs without this skill:

- its depth: one or two levels below the main thread;
- its contract and its scope; it writes nowhere else;
- its contract tests, read-only, and the test command;
- no staging or committing;
- the interfaces it depends on, pasted as text;
- every requirement the part owns, manifest and export updates included;
- only the settled decisions it touches;
- the names of the skills its work needs;
- the report format (section 8), and a request to report any decision a sibling may also face.

A part one level below the main thread may split again, so its brief adds: "If, after reading your part, you find sub-structure your parent could not have listed and holding it all would overload your context, load `recursio:splitting-implementation` before splitting; your own parts are at the depth limit and build." A part two levels below gets no split line, and its brief says it is at the depth limit and builds.

Keep briefs compact: never the whole plan or a sibling's code. [A part handed everything works from the plan instead of its scope.]

## 8. Reports

Each part reports:

- its outcome: split, built, or could not split;
- pass or fail as the command run and its terse output, never "all tests pass";
- the files it wrote;
- interface change requests;
- decisions a sibling may also face;
- "cannot satisfy the contract" with the reason, in place of editing a contract file or contract test.

## 9. Running a wave

- Spawn each part as the agent type that fits it best: general-purpose by default, a project or language agent when one fits the part's work. A part that may split again needs a type with the Agent tool.
- Spawn the wave's parts in one message, with no `name` and never as a fork. [With agent teams on, a named spawn becomes a teammate, which cannot nest; a fork inherits the whole conversation and gives no context relief.]
- Before spawning, record the changed-file list and a hash of each contract file and contract test; at the root, in split.md.
- Build nothing yourself while a part runs. [Your writes land in a part's scope and fail the scope check.]
- At the root, parts usually run in the background and report as notifications in later turns. Start the barrier only after every part listed under the wave in split.md has reported. [A barrier on half the wave passes code that is not there yet.]

## 10. At the barrier

Work through [barrier.md](barrier.md) once every part of the wave has reported. Code review is not the barrier's job.

## 11. split.md

The main thread keeps `.claude/workspace/<effort>/split.md`, following [split-template.md](split-template.md): the reload line, the settled decisions with their sources, the parts by wave, each barrier's result, what was decided without asking and what is left for the user. A part's own split lives in its context and its report, not in split.md.
