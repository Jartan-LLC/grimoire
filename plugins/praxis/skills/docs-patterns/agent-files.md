# Agent Instruction Files

CLAUDE.md, AGENTS.md, files they import or name as the rules (GUARDRAILS.md), `.claude/rules/`, and other tools' equivalents.

Ask the user before writing a convention the project has not settled (one seen only in git history); what the inputs state, or the task asks you to define, is settled. If nobody can answer, leave out only the unsettled part, keep what is settled around it, and say so in the PR description.

- Add a line only for what an agent here gets wrong without it (a command it cannot guess, a command form it would "simplify", a trap, a non-default practice, a layering or precedence rule no single file shows). Give the reason the project or failure gave where it decides cases the line leaves open.
- Where the project has settled a practice an agent's default breaks, state it as behaviour, not a setting's name: how PRs merge and which text lands, a commit or title form a tool reads, authorship lines, what commits and PRs must or must never contain, what needs approval.
- Where a tool ignoring `@` imports (Codex) reads the file, name each imported rules file in a sentence. Say which tool follows the import, never that it loads them "into every session".
- Point to what already states a fact (`make help`, `package.json`, the README, the file that registers a list) rather than copy it, and add the pointer when the change creates that source (new user docs, a new config file). No hand-kept count another file or the tree determines.
- In a template, mark each line a derived repo must change or delete, here or in its setup step; when adopting or syncing one, rewrite or delete each inherited line false here.
