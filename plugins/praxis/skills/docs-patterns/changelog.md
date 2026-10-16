# Changelog Entries and Release Notes

The project's own rules win where they speak (the agent instruction files, CONTRIBUTING, RELEASING, CHANGELOG.md's header). Follow CHANGELOG.md's format (headings, sections, credits, links), not what its other entries chose to include. If a tool builds the changelog from fragments, commit messages or PR titles, write what it reads.

Write each entry for someone upgrading who never saw the code, PRs or issues.

- Name each change by what users set, import, run or see (a command, flag, setting, output, what the agent does), leading with what changes for them.
- Describe a fix by what went wrong for users, since which release if known, and what happens now.
- Users may rely on what the project declares (README, changelog header, exports), else what its docs tell them to use, and in a template the files forks edit or run. Every change there gets an entry; any other only if users would notice it, saying what they might see.
- The rest is internal, even if importable: refactors, tests, CI, contributor tooling, docs edits that change no instruction, and release or dependency changes that leave what users install unchanged; a bump built or bundled into the release changes it. Leave it out unless the file or its tool keeps a section for it. If that leaves a required entry empty, write "No user-visible change."
- Leave out how a change was built or works inside (alternatives, review history, reviewer names, process labels).
- Something breaks when what worked on the last release fails or needs users to change something: a removal, rename, new or raised requirement (with its value). Mark it the file's way (else lead with "Breaking:") and put it first in its section. A changed default or output that still works is not a break: say what changes and how to keep the old behaviour. A fix that makes input users could pass before fail or return nothing is a break.
- Give every step an upgrade needs, breaking or not (a migration, a restart): what to do, old and new names, who does it, and before or after upgrading where order matters. A deprecation names its replacement.
- Name a vulnerability fix only in the release that ships it, with the affected versions and what to do (or the advisory), never with exploit detail; before then, describe it neutrally.
