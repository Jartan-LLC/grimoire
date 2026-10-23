# RELEASING.md and Release Procedures

The project's own rules win where they speak (agent instruction files, CONTRIBUTING.md, the release tool's configuration). Keep the procedure where, and in the form, the project keeps it (a checklist, docs page, another repository), else add it to CONTRIBUTING.md or contributor docs, asking the user first where the project has neither and naming their approval in the PR description. Edit only what this change makes wrong or missing, checked against the release workflows, scripts and settings it leaves; suggest other fixes in the PR description.

Write for a first-time releaser using this file and its links. Ask the user, rather than decide, what the project has not settled (when a version counts as released, whether a bad tag may move); what the inputs state is settled; what the task asks you to define, write and flag in the PR description as a proposal. If nobody can answer, leave out only the unsettled part, keep what is settled around it, and say so in the PR description.

- State what must exist or hold before the step that needs it (a tag the references name, CI green, access the inputs name), in that order. Where a step or schedule stops, say that it no longer happens.
- Where the project has bump rules, state them once: who or what picks the version and when, the levels in this project's terms, and every exemption. Never add SemVer levels the project does not state. Say what the version controls and when one counts as released where a reader would not guess. Where agent instruction files or CONTRIBUTING.md say when a bump is owed, keep that scope or point there.
- Give each fact a later change must keep true (a tag pattern the release workflow matches) a one-clause reason.
