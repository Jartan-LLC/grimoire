# Contributor Guides (CONTRIBUTING.md)

The project's own rules win where they speak. In CONTRIBUTING.md, add only rules the project has adopted or your change creates, never one inferred from history. Ask the user before writing a rule the project has not settled; what the inputs state, or the task asks you to define, is settled. If nobody can answer, leave out only the unsettled part, keep what is settled around it, and say so in the PR description. Keep its layout; put detail in any guide it points to. Unless your task is CONTRIBUTING.md itself, apply these lines only to what your change adds or makes false. State a rule's status (a trial, "for now") and a one-clause reason drawn from the inputs that a reader acts on. When syncing from a template, rewrite or delete each inherited line false here, and keep the true lines and the true parts of a line you rewrite; where the template and a project file disagree, state the project file's rule.

- State conventions the project requires but no tool reports (a commit or PR-title form, when a change earns a test and what it checks).
- Put maintainer-only chores under a "Maintaining" heading.
- If an agent file (CLAUDE.md, AGENTS.md or its imports) exists without loading CONTRIBUTING.md, add there, as its rules allow, one line per obligation or trap your change adds that no check catches: the whole condition, the action, "see CONTRIBUTING.md". Correct a line there your change makes false, without copying detail.
- Say which contributions you welcome, where to report a bug (one line), and that security issues go privately.
- Explain how to set up the development environment and run the tests, and whether a contribution needs tests.
- Explain how to submit a pull request: the branch it targets and what must pass before it lands.
- Say where to ask questions: the chat, forum or mailing list.
