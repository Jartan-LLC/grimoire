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

## Decisions
- <open decision or ask-first item> -- owner: <who> -- recommended: <...>
  -- default if unanswered: <option easiest to undo> -- if wrong: <what changes>
- Unchecked: <premise the plan rests on> -- if false: <what changes>

## Out of scope
- <change a reader would expect or an implementer be tempted to make> -- <issue, or "not planned">

## Steps
1. <change> in `path/file`, following `path/example:line`. <failure path and what handles it, if any>
2. ...

## Verification
- `<command>` -- passing shows <behaviour>.
- <manual check> -- look for <observable result>.
```

## Guidelines

- Approach: name only the alternatives a reader would raise, each with why not, and each review
  finding the plan declines, with why, so a later review sees it answered; leave out the Rejected
  line when there are none. A choice that is the planner's to make goes here with its reason.
- Decisions: decisions that belong to someone else and actions the project's rules say to ask about
  first, each with who owns it, the option you recommend, and the default the plan takes if no one
  answers: the option easiest to undo, never a guess at a fact about the owner's world, with what
  changes if it is wrong. A decision taken because no one could answer is recorded here as that
  default. Then each premise left unchecked on purpose. A premise that can be checked while planning
  is checked, not listed. Write "None." when there are none.
- Out of scope: only changes a reader would expect or an implementer be tempted to make, each with
  where it goes, and not work the change itself needs, such as sharing code with a caller that
  already exists. Leave out the section when there are none.
- Steps: concrete and in order, each ending in a state that can be checked, with the file to change
  and the existing code to follow (`file:line`). The docs, changelog entry and version bump the
  change owes are steps too, and, where a mistake would cost more than a revert, how the change
  reaches where it runs, its cost with a ceiling, and how it is undone. Put each failure path the
  plan found, and what handles it, in the step it affects.
- Verification: the strongest evidence that the change works, beyond the project's own Verify
  commands: each command or check, and what passing shows, the error cases too, seen where the
  change runs. A check that cannot fail is not evidence.
- If the plan is posted on GitHub, write no bare `#N`: GitHub links it to that issue or PR (see
  `gitwise:github-conventions`).
