# Reviewing agent instruction files

These checks cover a change to CLAUDE.md, AGENTS.md, the files they import or name as the rules, `.claude/rules/`,
and other tools' equivalents (`GEMINI.md`, `.github/copilot-instructions.md`, `.cursor/rules/`). Where the project's
own rules, checks or tools decide a point, raise nothing against them. Review against the skill's
`agent-files.md` (the writer's file, not this reference) first, then these checks.

A line that sends agents to a wrong recovery, migration or destructive step is Critical; tier the rest with
`review-severity`.

## The project's own rules

**Source file and how rules get added.** Look for an edit to a file the project says is not the source, or a rule
added in a way it forbids. An edit to a generated copy is lost at the next regeneration; a rule added
to a file the project says not to add to never reaches the tools that read the source. Verify: a generated file's
"do not edit" header and any line naming the source ("AGENTS.md files are the source of truth ... Do not add to
CLAUDE.md or Cursor rules."). Where the project routes rule changes through review ("Do not edit `.rules` inline
during normal feature/fix work"), an inline edit is the finding.

**The base branch's rules judge the PR.** A PR that changes the agent file's rule about PR descriptions: judge this
PR's own description by the rule on the base branch.

**Audience stated in the text.** Flag a rule for one audience (maintainers, staff, one tool) whose own text does not
name that audience; an agent outside it reads the rule as its own. Verify: read the rule without its heading. Better:
"Rules for merging pull requests (maintainers only):". Placement among sibling headings is not a finding.

## Claims and conventions

**Each new fact checked against the code.** Read the code path behind each new statement about behaviour, precedence
or loading; an agent obeying a wrong one acts with confidence. A claim narrowed from a code comment's contrast is
unverified until the code is read.

- Bad: "Only the global config directory may supply a `crushrc`." (the loader also reads `.crushrc` and `crushrc`
  from project directories, at higher priority)
- Better: point to the file that lists the names the loader reads.

**Conventions nobody settled.** Flag a new prescription no tracked file, check, issue or request states ("Commits
follow Conventional Commits." written from `git log`); later agents obey it as a project rule. Verify: search
CONTRIBUTING.md, the PR template and the CI config, then ask in the review whether it is the rule. A description of
practice ("Recent commits use ...; no file requires it") passes. When the PR description says a
convention was left out as unsettled ("I did not write 'update all three when you change a config option' into
AGENTS.md: only this PR shows that practice."), do not ask for the line; ask the maintainer.

## Pointers to other files and skills

**A trigger carries its whole condition.** A line for a rule another file owns must let an agent decide, from the
line alone, whether to act or open the file; an agent that must open the file to learn whether it applies will not.
The condition includes the one exception that decides it; levels, other exemptions and procedure stay with the
owner.

- Bad: "See CONTRIBUTING.md for contribution rules."
- Better: "A change under `migrations/` needs the schema dump regenerated; see CONTRIBUTING.md."
- Also good: "Read `.changeset/README.md` to determine whether a changeset is required and how to write it. Do not
  assume every package-code change needs one." The condition for opening the file is whole; the target decides the
  finer one.

**Sends to a skill or subagent that something else already brings.** Flag a line telling agents to load a skill or
run a subagent that a plugin hook, an agent's `skills:` list, a workflow step or a command already brings to that
moment; it drifts from its plugin. Verify: `.claude/settings.json` (`enabledPlugins`,
`hooks`), each enabled plugin's `hooks/hooks.json` and agent definitions where readable, and `.claude/commands/`. A
hook imperative injected on every prompt counts; a hook that fires after the text is written, or a skill's
description alone, does not. Where you cannot read a plugin, report the finding as suspected. Codex runs no Claude
Code hooks, so a pointer serving Codex sessions is not redundant.

**Rules about commit, PR, issue or review text load at session start.** That text has no file path, so a rule in a
path-scoped file never reaches the session writing it.

- Bad: `.claude/rules/git.md` with `paths: ["src/**"]` holding "PR titles name the package".
- Verify: each such rule, or its trigger, sits in the root agent file, an unscoped `.claude/rules/` file (Claude
  Code only), or a file they import; for Codex, in the AGENTS.md chain. A monorepo package's own rule in its own
  file passes.

**Imports.** `@path` outside backticks imports the file in Claude Code; check each `@` in prose was meant. Where
Claude Code reads the file, a rules file named only in a sentence is opened only if Claude decides to: suggest an
`@` import. Keep the sentence where Codex also reads the file; Codex follows no imports.

## Lines the change makes false

**Stale lines.** Search every file in scope (each agent file, each file it imports or names as the rules, other
tools' instruction files) for each command, flag, path, setting, make target and skill the diff renames, removes or
alters (`git grep -n '<old name>' -- '*CLAUDE.md' '*AGENTS.md' '*GEMINI.md' .claude/rules/ .github/ .cursor/rules/`).
Every later session follows a stale line. Delete a line that only copies what changed. Where
the rule still holds but names a renamed or removed thing, rename the thing and keep the rule. Unless the project
routes rule changes through review, a note in the PR description does not fix a stale line: the next agent reads the
file, not the PR.

- Bad: removing `eslint.config.js` from a "do not modify in passing" list once linting moved to `lint.config.ts`.
  Better: repoint the entry to `lint.config.ts`.
- Bad, and the common miss: keeping "Type-check, lint, full test suite must be green before any commit." in
  `cli/AGENTS.md` after the CLI lost its `lint` script and `pnpm run ci` stopped running type-check and lint.
  Better: "Type-check and lint (repository-wide: `pnpm -w type-check`, `pnpm -w lint`) and the full test suite must
  be green before any commit."

**Contradictions.** Check a rule the change adds against CONTRIBUTING.md, the PR template and the other agent files on
the same topic (`grep -ril '<topic>'`). An agent given two rules picks one arbitrarily. Fix each in the other file or
raise it in the PR description. Bad: the agent file says reasons go only in commit messages while the
PR template asks "What changed and why". A contradiction already present between two files the PR did not touch is
pre-existing: note it apart from this change's findings, addressed to the files' owners.

## Copies, overviews and lists

**Overview past one opening line.** Flag directory trees, file-by-file descriptions and architecture prose an agent
can read from the tree or the README; they go stale unseen. One identity line passes. Verify: compare each entry with
`git ls-files` and the README.

**Lists that copy their source.** Flag a list whose entries add nothing their source says: make targets with their
help text, skill names alone, a tool's file globs. A list whose entries each add when to use it passes. Where the
file itself asks for the list ("Add new skills to this list."), raise it against that rule, not the author. A
task-keyed map (each row a task, the file to read and when) passes; raise only its bare entries.

- Bad: "ESLint checks only JSON, YAML, TOML and Markdown" (copied from the ESLint config's file globs).
- Better: "Oxlint checks code; ESLint covers non-code files (see `eslint.config.mjs`)."

## True for a fresh clone

Flag notes on current work or a branch, session or branch links, and paths outside the repository; the next agent
reads them as standing rules or cannot open them.

- Bad: "## Current Active Work -- Branch: `rust-research`"; a link to the PR branch's docs
  (`.../tree/crushrc/docs/config`), dead once the branch is deleted.
- Better: point to `docs/config/` in the repository.

Not findings: a durable branch rule ("Branch names must start with `claude/`") and a line naming where to write
local files.

## Not findings

- Emphasis, tone, and the file's natural language.
- Length alone, unless a harness limit truncates the file (Codex stops reading at 32 KiB). Flag instead the lines
  that fail the writer file's "Add a line only for what an agent here gets wrong without it".
- Lines addressed to people in a file the project makes its AI policy for contributors.
- Tier labels and similar structure the project chose, and HTML comments kept as notes for humans (Claude Code strips
  block comments before loading the file).
- A rough figure given as a reason ("A full MR pipeline costs roughly 600 jobs").
