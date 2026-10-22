# Docs Pages (`docs/` and docs sites)

How-to, reference, explanation and tutorial pages, runbooks, operator guides and architecture pages. The project's own rules win where they speak. Unless your task is the page itself, apply these lines only to what your change adds or makes false.

- Write for the release a reader's install steps give them. Mark newer behaviour with its version, or as unreleased, and name versions by number ("servers before 0.2.0"), never "an earlier version" or "a version carrying this fix".
- Mark planned or target state where you state it, in the sentence or the section heading, with its issue. A note at the top of the page does not mark the lines below it.
- Give the page one reader and say its scope in its first lines: what it covers and which page has the rest. Where two readers need different parts, split the page or give each a section headed for them. Write the scope, not a label for the page's type.
- Title a how-to by its task. Order its steps as the reader does them, with each check before the step it decides, and put every action the task needs in the steps or link it from the step where it applies.
- A generated reference covers the surface the project supports; leave the rest out or label it internal.
- In a runbook, start each scenario with containment, then the fix, and end it with how to tell it is over and the step that undoes the containment.
- Name only files, settings and commands that exist, unless the line marks them planned. Where another page states the same setting, default or step, make the two agree, or point to one.
