---
name: planning
description: Planning work so the plan has fewer gaps -- sizing it to what a mistake would cost, finding what is missing and who settles it, checking premises against reality, seeing done where it runs, walking how it breaks, how it reaches the world, and an outside check when a mistake would be expensive.
when_to_use: Planning a change, feature, fix, migration, release or other piece of work before doing it -- in conversation, in a plan file or for an issue -- reviewing someone else's plan, or revising a plan when the work contradicts it.
user-invocable: false
---

# Planning

A plan exists to find what is missing while it is still cheap to fix. The sections below are ways of
thinking, not plan headings: put in the plan only what changes what gets built or checked. A short plan
whose premises were checked beats a long one whose were not.

## Size the plan to what a mistake would cost

Two questions set the effort: how hard is this to undo, and how clear is what to build? A plan for an
easy-to-undo change with a clear outcome says what changes and how done is seen, and nothing about
rollout, risk, cost or undo -- not even a line saying none is needed or that a revert undoes it. Spend
more where a mistake lands outside the diff -- data and user state, secrets and permissions, CI and
release gates, public interfaces and their callers, money, anything shipped to other people -- and where
what to build is unclear. More planning is not safer: steps the work does not need make outcomes worse.

## Find what is missing, and who settles it

Before designing, ask what you would need to know to call this done, and whether the request, the
repository or the project's rules and notes already say. Gaps get filled silently with something
plausible: look for them on purpose. When a request names only a solution, find the problem it solves.
Then give each gap to whoever owns it:

- A fact -- how the code, a tool or the environment behaves -- is settled by looking: read it, run it,
  reproduce it. Do not ask a person what you can check.
- A choice inside the work is yours: make it, with its reason in a line.
- A decision about what to build, for whom, at what cost or risk, or one that commits other people,
  belongs to whoever owns that outcome: ask them. If the evidence says the request will miss its own
  goal, say so.

Which kind a gap is does not follow from who usually decides: a user may own a technical constraint (how
they merge, what they run), and the project's rules may already answer what looks like a product
question. Ask early and ask few, each question self-contained: the options, what each costs, and which
you would pick. Do not offer a guess about the owner's own world as a default.

## When no one can answer

A headless run, a subagent, an away user: do not stop. For a decision someone else owns, take the option
easiest to undo that you would defend, record it as an assumption with what changes if it is wrong, and
continue. Hold back only the steps that cannot be undone and rest on such an assumption, unless the owner
has told you to decide. Put the assumptions where the person will look first.

## Check premises against reality

Rereading a plan rarely finds its errors; observing something does. For each premise the plan stands on
-- the cause of a bug, what a tool does, what the code already does, how the people involved work -- make
the cheapest observation that would show it false, before building on it, or say it is unchecked and
what changes if it is false.

## See done where it runs, and walk how it breaks

Write done as something observable, the error cases included, seen in the environment the work really
runs in. A check that cannot fail checks nothing. Trace one real case through what the change touches,
then what breaks it: interrupted halfway, run twice or at once, odd input, a dependency down. Look
hardest where state cannot be taken back, and put each failure that applies, with what handles it, in
the step it affects: a failure class left for review is found one round at a time.

## Plan how it reaches the world

Where a mistake would cost more than a revert, say how the work gets to where it runs and in what order
with other work in flight; who else it touches and whether they must be told, migrated or credited;
what it costs, judged from similar work, with a ceiling and a leaner option; and how it is undone.

## Get an outside check when a mistake would be expensive

When a change is hard to undo or what to build is unclear, have someone who did not write the plan -- a
fresh agent will do -- check it against this skill and the request, observing where a premise can be
checked, and report only what would change the work. An open hunt always finds something: revise only
for what holds, and check again until a round finds nothing that would change the work.

## Keep the plan true while working

When the work contradicts a premise, change the plan before going on; when an estimate is crossed,
estimate again. When a second fix lands on the same spot, or each review round finds a new kind of
problem, stop patching: the plan is missing a failure class or sits at the wrong level.
