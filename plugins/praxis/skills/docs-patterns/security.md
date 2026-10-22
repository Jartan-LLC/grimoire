# Security Policies (SECURITY.md)

The project's own rules win where they speak. Ask the user before writing a channel, a promise or a supported-versions rule the project has not settled; what the inputs state, or the task asks you to define, is settled. If nobody can answer, leave out only the unsettled part, keep what is settled around it, and say so in the PR description. Edit the file GitHub shows: `.github/SECURITY.md`, else the root, else `docs/`, else the owner's `.github` repository, whose file covers every repository without its own. Unless your task is the policy itself, apply these lines only to what your change adds or makes false, and keep the lines your task does not touch.

- Name a private channel that works for every repository the file covers. GitHub private vulnerability reporting must be on in each (`gh api repos/OWNER/REPO/private-vulnerability-reporting`); a service must still take this project's reports. Give the reporter's steps: the repository's Security tab, then "Report a vulnerability". Where private reporting is on, say so even when another channel comes first.
- Say which versions get security fixes as a rule tied to releases ("the latest minor release of 2.x"). A table of versions must include the current release and list only versions that exist.
- Promise no response time, fix deadline, disclosure window, bounty or safe harbor the maintainers have not chosen. A template's numbers ("within 3 working days", "90 day") are not their choice.
- Say what is not a vulnerability here only where the project has a stance: trusted inputs, a threat model, issues that belong upstream.
- Tell reporters to keep reports out of public issues, pull requests, discussions and any chat the project links.
- Keep a what-to-include list short and fit for every channel the file names. Where reports go only through GitHub's form, add none: the form asks.
- When the channel or a program changes, update every line that refers to the old one ("the addresses above", bounty terms).
- Leave no template text: the "Use this section to tell people..." prompt, `$VMTalias`, example version rows.
