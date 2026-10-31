# split.md template

The main thread writes `.claude/workspace/<effort>/split.md` before the first spawn and updates each part's status as it reports. Keep the first line as it is.

```markdown
If the splitting skill was lost to compaction, load `recursio:splitting-implementation` again and resume from the status lines below.

# Split: <task>

## Settled decisions

- <decision> -- source: <the project, the parent or plan, or decided here>

## Wave 1

Snapshot before spawning: <each file `git status --porcelain -uall` lists, with its `git hash-object`>; contract hashes: <`git hash-object` of each contract file and contract test>

### <part>

- Owns: <files or directories>
- Depends on: <parts or interfaces>
- Contract: <file or interface>
- Contract tests: <files>, run with `<command>`
- Agent type: <general-purpose, or the project or language agent that fits>
- Status: <pending, running, reported, passed or failed>
- Outcome: <split, built or could not split>

### Barrier

<commands run and their outcome; divergences settled; retries>

## Wave 2

...

## Decided without asking

- <decision> -- <its source or reason>

## Left for the user

- <item and why it was left>
```
