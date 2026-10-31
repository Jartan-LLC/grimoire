# Brief template

A level writes each part's brief from this, keeping only the depth line that applies.

```markdown
# Brief: <part>

Depth: <one | two> level(s) below the main thread.
<one level below:> After reading your part, if it may hold sub-parts that each are real work, load `recursio:splitting-implementation` and decide with its section 1 gate whether to split; your own parts are at the depth limit and build.
<two levels below:> You are at the depth limit: build your part and never split.

Scope: write only <files>; everything else is read-only.
Contract, read-only: <files>. Contract tests, read-only: <files>.
Test command, your tests only: <command>
Requirements: <where each is written: spec section, issue>
Interfaces you depend on:
<pasted as text>
Settled decisions you touch: <list>
Skills to load: <names>
Do not stage, commit, push or switch branches. Ask no questions; report instead.

Report: outcome (split, built, or could not split); the test command and its terse output; files written; interface change requests; decisions a sibling may also face; "cannot satisfy the contract" and why, in place of editing a contract file or test.
```
