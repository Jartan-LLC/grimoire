# Implementation Plan Format

Three readers use the plan:

- the user, deciding whether to approve it;
- the agent implementing it, often in a later session with only the issue, the plan and the repo;
- `create-pr`, checking the diff against it.

Write nothing the issue already says.

## Template

```markdown
# Plan: <issue title> (issue <n>)

## Approach
What changes and why this way, in a few sentences, and the trade-off it accepts.
Rejected: <alternative> -- <why not>. (omit when none)

## Decisions for the user
- <open question or ask-first item> -- default if unanswered: <...>
- Assumption: <fact the plan rests on that could be false> -- if false: <what changes>

## Out of scope
- <change a reader would expect or an implementer be tempted to make> -- <issue, or "not planned">

## Steps
1. <change> in `path/file`, following `path/example:line`. <hazard, if any>
2. ...

## Verification
- `<command>` -- passing shows <behaviour>.
- <manual check> -- look for <observable result>.
```

## Guidelines

- Approach: name only the alternatives a reader would raise, each with why not; leave out the
  Rejected line when there are none.
- Decisions for the user: open questions, actions the project's rules say to ask about first, and
  assumptions, each with the default the plan takes. Write "None." when there are none.
- Out of scope: only changes a reader would expect or an implementer be tempted to make, each with
  where it goes, and not work the change itself needs, such as sharing code with a caller that
  already exists. Leave out the section when there are none.
- Steps: concrete and in order, each ending in a state that can be checked, with the file to change
  and the existing code to follow (`file:line`). The docs, changelog entry and version bump the
  change owes are steps too. Put a hazard in the step it affects.
- Verification: the strongest evidence that the change works, beyond the project's own Verify
  commands: each command or check, and what passing shows.
- If the plan is posted on GitHub, write no bare `#N`: GitHub links it to that issue or PR (see
  `gitwise:github-conventions`).
