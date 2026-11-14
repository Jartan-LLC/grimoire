# Grading specs: plain-writing sizing cases (issue 182)

One section per case: dev (1-8), screen (S1-S10) and confirm (C1-C9). A case added later gets
its section before its docs are graded (suite.toml). A grader reads the doc the writer produced
(the target file's final text, or the diff to it), checks it against the items below, and gives
one label.

Each spec was written blind, before any doc of its case was graded, from the case's prompt.md,
fixture/ and build.py and the rule (the plain-writing paragraph "Write for what the reader does"
and its "Always keep" list), without seeing any model output or the case's key.toml, reference/
or fix/. For the screen and confirm specs the rule also took in, where the doc type needs it,
docs-patterns' SKILL.md and its readme.md, docs-pages.md or releasing.md; they are kept as the
panel graded with them. The one exception to blind writing is walkaway-readme's M4 and B3, set
after the dev smoke to follow the last "Always keep" item.

Case paths below are relative to `tests/evals/praxis/skills/plain-writing/cases/<case>/`.
"commit N" means the Nth entry of the COMMITS list in that case's build.py (the branch the writer
worked on). "SKILL.md:N" is a line of plain-writing's SKILL.md as these specs were graded against
it, before its warning sentence gained a line: from line 31 on, the same text now sits one line
later. Two rule lines decide most screen and confirm items: SKILL.md:24-25 ("What the program handles on its own
-- a case it skips, fixes or reports with its own remedy -- needs no line") and SKILL.md:28-30 (a
warning before data loss, a leaked secret or a step that cannot be undone "stays where the reader
acts, however rare").

## Labels

- **right-sized**: every MUST item is present, each WARNING (W) sits where the reader
  acts (before or at the step it guards, not only at the end of the doc), and no BLOAT
  item appears. Length follows from the MUST items; the rough size guide in each case is
  a sanity check, not a target.
- **bloated**: every MUST item is present and placed right, but one or more BLOAT items
  appear (any line or clause that states one counts), or the added text pads the doc with
  material the sources do not state and no reader acts on.
- **under**: one or more MUST items are missing (or stated so vaguely the reader cannot
  act on them, e.g. a command without its exact form), and no BLOAT item appears. A
  missing W is the most serious form of under.
- **mis-sized**: either (a) BLOAT present and a MUST missing, or (b) the right content in
  the wrong place: a W moved away from its step (for example only in a closing notes
  section), recovery from a rare failure set in the main path instead of a short
  troubleshooting part at the end, or a prerequisite stated after the steps it serves.

Precedence: decide on MUST and placement first, then BLOAT. A misplaced W with nothing
missing and no bloat is mis-sized, not right-sized.

General notes for every case:

- Judge only text the change writes, or existing text it makes false. Existing correct
  content the writer leaves untouched is not graded. Existing correct content the writer
  deletes without being asked counts as a missing MUST.
- UNSURE items never decide a label on their own. Note them in the grading rationale.
- NEUTRAL items do not change the label either way.
- A short troubleshooting part at the end holding a rare failure the reader must act on is
  correct placement, not bloat.
- Invented specifics the sources do not state (a token variable name, a flag, a step
  order) are an accuracy note. If they add a paragraph or more that no reader acts on,
  count them as bloat.

---

## 1. prune-warning

- **Target doc**: `docs/usage.md` (existing; sections for `snap take` and `snap list`).
- **Request** (prompt.md): "Document the prune command in docs/usage.md."
- **Reader and normal job**: a snap user who wants to free space by removing old
  snapshots. They pick between keeping the newest N and deleting all, then run the
  command.

### MUST

- M1. The command forms, exact: `snap prune --keep N` (deletes all but the newest N
  snapshots) and `snap prune --all` (deletes every snapshot). Source:
  fixture/snap/cli.py USAGE lines 6-7.
- M2. The choice between them: `--keep N` keeps the newest N, `--all` removes every
  snapshot. Source: fixture/snap/cli.py lines 6-7.
- M3 (W). `--all` deletes the latest snapshot too, and this cannot be undone. Stated at
  the `--all` form or before it, not only at the end. Source: fixture/snap/cli.py line 7
  ("delete every snapshot, the latest included; this cannot be undone").

### BLOAT

- B1. A snapshot whose directory vanished mid-prune is skipped (the program handles it).
  Source: build.py commit 1 (snap/prune.py docstring).
- B2. Two prunes running at the same time / concurrency. Source: build.py commit 1 body.
- B3. Narration of the branch or its fix commit ("this branch adds", "now skips").

### NEUTRAL

- N1. A heading `## snap prune` matching the existing sections.
- N2. Saying deletion by `--keep N` is also permanent. The source states "cannot be
  undone" only for `--all`; extending it to deletion in general is a reasonable reading,
  not a fabrication. UNSURE whether a strict grader would call it an unsupported claim;
  do not mark it either way.

### Label guidance

- Right-sized: a section about the size of the existing ones, roughly 3 to 6 lines: both
  forms, what each keeps, and the `--all` warning beside the `--all` form.
- Bloated: M1-M3 present plus the vanished-directory skip or concurrency talk.
- Under: the "cannot be undone" or "latest included" warning missing, or only one form
  documented.
- Mis-sized: the warning only in a trailing note away from the command, or B1/B2 present
  with M3 missing.

---

## 2. publish-recovery

- **Target doc**: `RELEASING.md` (existing; three numbered steps: bump and changelog,
  merge, tag and push).
- **Request** (prompt.md): "Add the publish step to RELEASING.md."
- **Reader and normal job**: a maintainer cutting a release who follows the numbered
  steps in order and publishes the wheel to PyPI.

### MUST

- M1. The exact command: `make publish` (it builds the wheel and uploads it to PyPI with
  twine). Source: fixture/Makefile lines 3-5.
- M2 (W). PyPI never accepts the same version twice: an upload cannot be redone under the
  same version. Stated at or before the publish step. Source: fixture/Makefile lines 1-2.
- M3. Recovery from a broken upload: yank it on PyPI and release the next patch version.
  Source: fixture/Makefile lines 1-2. Placement: at the publish step (with M2) or in a
  short troubleshooting part at the end; either is correct. UNSURE whether a broken
  upload is "rare" in the rule's sense; because M2 is a warning about an irreversible
  step and M3 is its only remedy, keeping them together at the step is the safer reading,
  and an end-of-doc troubleshooting entry for M3 is also acceptable as long as M2 stays at
  the step.
- M4. The step fits the numbered list (a new step 4, or inserted in sequence) without
  breaking the existing steps. Source: fixture/RELEASING.md.

### BLOAT

- B1. twine's clock-skew warning on hosts without network time, or that it is silenced.
  The program handles it. Source: build.py commit 1 (scripts/publish_env.py).
- B2. Restating the Makefile internals at length (`python3 -m build`, `twine upload
  dist/*`) as separate steps the reader runs instead of `make publish`. A short clause
  saying what `make publish` does is NEUTRAL.
- B3. Branch or fix-commit narration.

### NEUTRAL

- N1. Whether publish is placed after the tag step or between merge and tag. The fixture
  gives no order; do not grade it.
- N2. A clause saying what `make publish` does (builds and uploads).
- N3. Credentials for PyPI. The fixture says nothing about them. A bare "needs PyPI
  upload rights" is neutral; an invented token variable or config file is an accuracy
  note (see general notes).

### Label guidance

- Right-sized: one added step, roughly 1 to 4 lines, carrying the command, the
  same-version warning and the yank-and-bump remedy.
- Bloated: M1-M4 present plus anything about twine's clock warning.
- Under: M2 or M3 missing (a step that just says `make publish`).
- Mis-sized: M2 only in a closing section away from the step; or the clock-warning text
  present with M2/M3 missing.

---

## 3. backup-commands

- **Target doc**: `docs/commands.md` (existing; sections for `vault init` and
  `vault status`).
- **Request** (prompt.md): "The backup and restore commands on this branch are done. Add
  them to docs/commands.md."
- **Reader and normal job**: a vault user who backs up their vault directory to a
  destination and later restores from an archive.

The final code is build.py commit 5's `vault/backup.py`; the CLI is fixture/vault/cli.py.

### MUST

- M1. `vault backup DEST`: writes a dated `.tar.gz` archive of the vault into DEST.
  Exact form. Source: fixture/vault/cli.py line 11; build.py commit 1 body.
- M2. `vault restore [ARCHIVE]`: unpacks ARCHIVE into the vault. Exact form. Source:
  fixture/vault/cli.py line 12.
- M3. The restore choice: give ARCHIVE, or omit it to restore the newest archive in DEST
  (the DEST of the last successful backup, which the vault records). Source:
  fixture/vault/cli.py line 12; build.py commit 5 `restore()` and `backup()` writing
  `.vault/dest`. Saying "the newest archive in DEST" is enough; "last successful backup"
  wording is a plus, not required.

### UNSURE (could be MUST)

- U1. Prerequisite: backup and restore need GNU or BusyBox tar. Source:
  fixture/vault/cli.py lines 21-23. The rule keeps "prerequisites, before the steps they
  serve", but also says what the program "reports with its own remedy needs no line", and
  the CLI prints exactly this message and exits. Either reading is defensible: present is
  not bloat, absent is not under.
- U2 (possible W). Restore unpacks over the files in the vault: files that changed since
  that backup are replaced by the archive's copies. Derived from `tar -xzf` into `.` in
  build.py commit 5 `restore()`; the fixture never states it. A line like this, ideally
  pointing at `vault status` (fixture/docs/commands.md line 9) to check first, is a good
  addition; its absence is not under, because no source states the overwrite.
- U3. Backup fails (non-zero exit, no archive written) when a file changes while tar reads
  it; the reader reruns. Source: build.py commit 4 (exit 1 now a failure). tar prints its
  own message. If included, it belongs in a short troubleshooting part at the end;
  in the main path it is mis-placed; absent is fine.

### BLOAT

- B1. `.part` files: the temporary name, or that leftovers older than a day are swept.
  Source: build.py commit 3.
- B2. Picking the newest archive by the date in its name rather than mtime / the clock
  running ahead. Source: build.py commit 2.
- B3. Setting the top directory's mode and mtime from the archive / GNU vs BusyBox
  difference there. Source: build.py commit 5.
- B4. tar padding a shrunk file with zeros, or exit-code internals (exit 1 and what it
  meant before). Source: build.py commit 4. (U3's one-line rerun advice is not B4; the
  explanation of why is.)
- B5. Branch or fix-commit narration.

### NEUTRAL

- N1. The archive name pattern `vault-YYYYMMDD-HHMMSS.tar.gz` (helps a reader pick an
  ARCHIVE). Source: build.py commit 1 body and code.
- N2. Running the commands from the vault directory (both act on `.`).
- N3. Headings `## vault backup` / `## vault restore` matching the existing sections.

### Label guidance

- Right-sized: two sections about the size of the existing ones, roughly 4 to 10 lines in
  all, covering M1-M3; optionally U1/U2 and a one-line U3 at the end.
- Bloated: M1-M3 present plus any of B1-B4.
- Under: restore's default (M3) missing, or a command without its argument form.
- Mis-sized: any B item present with a MUST missing; or U3 recovery written into the main
  backup section as a procedure.

---

## 4. settings-table

- **Target doc**: `docs/config.md` (existing; a table of settings in `queue.toml` with
  Setting / Default / What it sets columns).
- **Request** (prompt.md): "Add the settings this branch adds to docs/config.md."
- **Reader and normal job**: an operator editing `queue.toml` who scans the table for a
  setting's name, default and effect, and decides whether to change it.

### MUST

- M1. A row for `lock_timeout`, default `30`, seconds to wait for the queue lock. Source:
  build.py commit 1 (queue/settings.py).
- M2. When to change it: raise it on slow network disks. Source: build.py commit 1
  comment ("raise it on slow network disks"). This is a "which option fits which case"
  condition.
- M3. A row for `fsync_every`, default `0`, fsync the journal every N jobs. Source:
  build.py commit 1.
- M4. What `0` means: leaves syncing to the OS. Source: build.py commit 1 comment.
- M5. The rows follow the existing table format (same columns). Source:
  fixture/docs/config.md lines 5-8.

### BLOAT

- B1. Byte order mark handling, Notepad, `utf-8-sig`, tomllib rejecting the file. The
  program handles it. Source: build.py commit 2.
- B2. A durability or performance discussion of `fsync_every` beyond the source comment
  (crash safety, throughput trade-offs). The sources do not state it. UNSURE: a few words
  like "lower is safer" are a reasonable inference but still unsourced; a paragraph is
  bloat.
- B3. A new prose section or example `queue.toml` block repeating what the table rows
  say. UNSURE if short (one example block); a separate section per setting is bloat.
- B4. Branch or fix-commit narration.

### NEUTRAL

- N1. Units written as "seconds" in the cell, or "30 s".
- N2. Row order.

### Label guidance

- Right-sized: two table rows, nothing else changed (about 2 lines added).
- Bloated: both rows plus BOM notes, a durability paragraph, or per-setting prose
  sections.
- Under: a row missing, a default missing, or M2/M4 dropped from the description.
- Mis-sized: B1 present with M2 or M4 missing; or the rows added outside the table with
  the guidance split from the setting it qualifies.

---

## 5. merge-readme

- **Target doc**: `src/dotmerge/README.md` (existing; one-line intro and an Install
  section).
- **Request** (prompt.md): "Update the dotmerge README for the merge behaviour this
  branch adds."
- **Reader and normal job**: a team member adding the dotmerge feature to their dev
  container, who needs to know what it will do to their own settings file and how to get
  their original back.

### MUST

- M1. At container start, dotmerge merges the team (image) settings into
  `~/.config/tool/settings.json`. Source: build.py commit 1 subject and install.sh;
  fixture/src/dotmerge/devcontainer-feature.json description.
- M2. On a conflict the user's values win. Source: build.py commit 1 body.
- M3. The original file is kept as `settings.json.pre-dotmerge` (the reader's way back).
  Source: build.py commit 1 body; devcontainer-feature.json description. Not a W in the
  strict sense (nothing is lost, the original is kept), but it is the recovery the reader
  needs, so it is required.
- M4. The existing Install section stays intact. Source: fixture/src/dotmerge/README.md.

### BLOAT

- B1. Following a symlinked `settings.json` / dotfile managers. The program handles it.
  Source: build.py commit 4.
- B2. A `settings.json` that is not valid JSON is left untouched with a message. The
  program reports it with its own message. Source: build.py commit 5.
- B3. Narrating that `.pre-dotmerge` used to be overwritten on a second start. Source:
  build.py commit 2. (A short clause that the backup is taken once and never replaced is
  NEUTRAL, see N1.)
- B4. Branch or fix-commit narration.

### UNSURE

- U1. `settings.json.held` left by an interrupted merge, which deactivation leaves in
  place. Source: build.py commit 3. It is rare and no source says what the reader does
  with it, which leans BLOAT; but a reader who finds the file may need to know it holds
  their data. If included, it belongs in a short troubleshooting part at the end; in the
  main description it is mis-placed.

### NEUTRAL

- N1. "The original is copied once, on the first start, and never replaced." Source:
  build.py commit 2 code.
- N2. A heading such as `## What it does` or `## Merge behaviour`.
- N3. How to restore (copy `.pre-dotmerge` back over `settings.json`): a natural reading of
  M3, not stated in the sources; one line is fine.

### Label guidance

- Right-sized: a short section, roughly 2 to 5 lines, covering M1-M3, with Install kept.
- Bloated: M1-M3 present plus symlink handling, invalid-JSON handling, or fix history.
- Under: M2 or M3 missing (the reader cannot tell whose values win or how to get the
  original back).
- Mis-sized: B items present with M2/M3 missing; or U1 placed in the main description as
  if it were normal behaviour.

---

## 6. walkaway-readme

- **Target doc**: `README.md` (existing; intro and Install section). No build.py: the
  command already exists in fixture/commands/walkaway.md.
- **Request** (prompt.md): "Add the walkaway command to the README."
- **Reader and normal job**: a plugin user deciding whether to start the command before
  stepping away, and what state they will come back to.

### MUST

- M1. The command to run: `/walkaway`. Source: fixture/commands/walkaway.md (file name,
  frontmatter). UNSURE on exact form: Claude Code may show plugin commands namespaced as
  `/autopilot:walkaway`; either form is acceptable, a missing invocation is not.
- M2. What it does: runs review rounds on the current branch's PR until two come back
  clean, then stops. Source: fixture/commands/walkaway.md line 5.
- M3. Hard constraints the reader relies on while away: never pushes to `main`, never
  merges, never force-pushes. Source: fixture/commands/walkaway.md line 9.
- M4. A pointer to `commands/walkaway.md` for the full list of limits, or the whole list
  (which names B3's skip cases). A doc that lists some limits without the pointer says its
  list is partial; a silently partial list is a MUST failure. Source: fixture/commands/walkaway.md lines 7-13; the rule's last "Always
  keep" item.

### UNSURE (each could be MUST or BLOAT)

- U1. `gh` must be logged in, or the run is skipped. Source: walkaway.md line 12. The rule
  calls "a case it skips" something that needs no line, but this one is a prerequisite
  the reader must meet before leaving, and the reader is away when the skip happens. Leans
  MUST as a prerequisite; graders should not mark under for its absence if M4's pointer
  is given.
- U2. Stops after 8 rounds (the reader may come back to an unfinished review). Source:
  walkaway.md line 10. Covered by M4's pointer when absent.

### BLOAT

- B1. Explaining how review rounds work internally, what "clean" means beyond the source,
  or which reviewers run: none of it is in the sources.
- B2. Restating the Install section or the plugin intro.
- B3. Naming a case the command skips on its own: a PR from a fork, or draft PRs older
  than 30 days, in prose or as items of a copied Limits list. Source: the rule, "a case it
  skips ... needs no line", and the last "Always keep" item: a whole list is kept when the
  reader acts on it, and for cases the program handles on its own a pointer to where they
  are listed is enough.

### NEUTRAL

- N1. A `## Commands` or `## walkaway` heading.

### Label guidance

- Right-sized: a short section, roughly 3 to 10 lines: invocation, what it does, the
  never-push/merge/force-push guarantees, and a pointer to commands/walkaway.md.
- Bloated: M1-M4 present plus invented internals, padding, or B3.
- Under: M1, M2, M3 or M4 missing (a partial limits list with no "partial" note and no
  pointer is M4 missing), and no BLOAT item.
- Mis-sized: a BLOAT item present with M1, M2, M3 or M4 missing.

---

## 7. secret-in-archive

- **Target doc**: `docs/backup.md` (new file; the docs folder has only `docs/index.md`).
- **Request** (prompt.md): "Write docs/backup.md for the backup and restore commands."
- **Reader and normal job**: a relay CLI user who backs up their relay configuration and
  later restores it, and who will store or move the archive somewhere.

### MUST

- M1. `relay backup [FILE]`: writes `~/.config/relay` into FILE, default
  `relay-backup.tar.gz`. Exact form. Source: fixture/relay/cli.py line 1.
- M2. `relay restore FILE`: unpacks it. Exact form. Source: fixture/relay/cli.py line 1.
- M3 (W). The archive holds `credentials.json`, which holds the API token: anyone with the
  archive can use the token. Stated at or before the backup command (where the reader
  creates the archive), not only in a closing section. Source: fixture/relay/backup.py
  line 3. This is the case's central warning; a missing or moved M3 is the most serious
  failure.

### BLOAT

- B1. Archives over 4 GiB are split for BusyBox tar. The program handles it. Source:
  build.py commit 1 (relay/split.py).
- B2. Branch or fix-commit narration.

### UNSURE

- U1. What to do if the archive leaks (revoke or rotate the token). No source says how.
  A one-line "treat the archive like the token; revoke the token if it leaks" is a
  reasonable addition, not required; a procedure with invented steps is an accuracy note.
- U2. Whether restore overwrites an existing `~/.config/relay`. No source states it. Do
  not require it; an invented claim either way is an accuracy note.
- U3. How to restore a split archive (more than one file). The split exists
  (build.py commit 1) but nothing says how restore handles it, and a config folder over
  4 GiB is far outside normal use. Leans BLOAT; absent is fine.

### NEUTRAL

- N1. A title and one-line intro.
- N2. Advice on where to keep the archive (outside the repo, not shared), as long as it
  stays a short expansion of M3.
- N3. A link from `docs/index.md` (the prompt does not ask for one).

### Label guidance

- Right-sized: a short page, roughly 5 to 12 lines: title, the two commands with their
  forms and default, and the token warning at the backup command.
- Bloated: M1-M3 present plus the 4 GiB split detail.
- Under: M3 missing, or a command form or the default file name missing.
- Mis-sized: M3 only in a trailing "Notes" or "Security" section after both commands; or
  B1 present with M3 missing.

---

## 8. release-tags

- **Target doc**: `RELEASING.md` (existing; two sentences on bumping a package's version
  with a changelog entry).
- **Request** (prompt.md): "Document how to tag a release in RELEASING.md now that
  scripts/tag-release.sh exists on this branch."
- **Reader and normal job**: a maintainer of the monorepo who, after version bumps land,
  runs the tagging script and needs to know what it does and how to recover if the push
  is refused.

The final script is build.py commit 5's `scripts/tag-release.sh`.

### MUST

- M1. The exact command: `scripts/tag-release.sh` (or `sh scripts/tag-release.sh`).
  Source: build.py commit 1.
- M2. What it does: tags each package version that has no tag yet as
  `<name>--v<version>`, then pushes the tags. Source: build.py commit 1 subject, body and
  script comment. The tag name format and the fact that it pushes are both required.
- M3. Recovery from HTTP 403 on push: a token issued before a workflow file changed is
  refused; run `gh auth refresh -s workflow`, then rerun the script. Exact command.
  Source: build.py commit 2 body and script comment. Placement: a short troubleshooting
  part at the end (the failure happens only after a workflow change). At the run step as a
  one-line "if push fails with 403" is acceptable; a multi-line explanation in the main
  steps is mis-placed.

### UNSURE

- U1 (possible W). The script pushes tags itself; a pushed tag is visible to others at
  once. No source calls it irreversible. Stating plainly that the script pushes (M2)
  satisfies the need; a separate "cannot be undone" warning is an unsupported claim, but
  harmless if short.
- U2. The script runs `make verify` first and stops if it fails (`set -eu`). Source:
  build.py commit 1 script. The reader runs nothing extra because of it; leans NEUTRAL.
  If the doc tells the reader to run `make verify` themselves first, that is NEUTRAL too
  (AGENTS.md line 5 already requires it for changes).

### BLOAT

- B1. Versions 1.5.0 and earlier are skipped (predate per-package changelogs). The program
  handles it. Source: build.py commit 3.
- B2. `make verify` now accepts caret, tilde, equals and exact ranges. Unrelated to tagging
  and handled by the program. Source: build.py commit 4.
- B3. The tag push no longer waits for the dev container build. Program behaviour the
  reader takes no action on. Source: build.py commit 5.
- B4. Branch or fix-commit narration.

### NEUTRAL

- N1. When to run it (for example after the version-bump PR merges). The fixture does not
  say; a short sensible statement is neutral, an invented multi-step procedure is an
  accuracy note.
- N2. A `## Tagging a release` heading.

### Label guidance

- Right-sized: a short section, roughly 3 to 8 lines: the command, what it tags and that
  it pushes, and the 403 recovery in a short troubleshooting part at the end (or one line
  at the step).
- Bloated: M1-M3 present plus any of B1-B3.
- Under: M3 missing, or the tag format or the push missing from M2.
- Mis-sized: B items present with M3 missing; or the 403 recovery written into the main
  steps as a procedure.

---

## S1. cronlite-doc

- **Target doc**: `docs/schedule.md` (new file; the fixture has no `docs/` folder).
- **Request** (prompt.md): "Write docs/schedule.md: how to schedule, list and remove
  jobs."
- **Reader and normal job**: a cronlite user who adds a scheduled command, checks what is
  scheduled, and removes a job.

### MUST

- M1. The three command forms, exact: `cronlite add SCHEDULE COMMAND`, `cronlite list`,
  `cronlite remove ID`. Source: fixture/cronlite/cli.py:1.
- M2. SCHEDULE is a five-field cron expression in local time. Both "five-field cron" and
  "local time" are required: the time zone decides when the job runs. Source:
  fixture/cronlite/cli.py:1.

### BLOAT

- B1. A job still running at its next start is skipped. The program handles it. Source:
  commit 1 (subject and cli.py comment).
- B2. February 29 schedules run only in leap years. The program handles it. Source:
  commit 3.
- B3. Branch or fix-commit narration ("this branch fixes", "now skips").

### UNSURE

- U1. With no `/etc/localtime` (slim containers) schedules run in UTC. Source: commit 2.
  The program handles it (falls back), which leans BLOAT; but a reader in a slim
  container who writes `0 9 * * *` expecting local time gets a wrong result
  (SKILL.md:17-18), and nothing says the program reports the fallback. A one-line
  qualifier at M2 is defensible; a paragraph is bloat. Absent is not under.

### NEUTRAL

- N1. That `remove` takes the ID that `list` shows. Not stated in the source, but the
  natural reading; one clause is fine.
- N2. An example cron expression (for example `0 9 * * *`).
- N3. A title and one-line intro; a link from elsewhere (none is asked for).

### Label guidance

- Right-sized: a short page, roughly 4 to 10 lines: the three forms and the
  five-field/local-time note, optionally one example.
- Bloated: M1-M2 present plus B1 or B2, or explanation of cron syntax a cron user
  already knows (SKILL.md:59) at more than a line.
- Under: a command missing, or "local time" missing from the SCHEDULE description.
- Mis-sized: B1/B2 present with M1 or M2 incomplete.

---

## S2. export-howto

- **Target doc**: `docs/export.md` (new file; the docs folder has only `docs/index.md`).
- **Request** (prompt.md): "Write a how-to page, docs/export.md, for exporting a ledger."
- **Reader and normal job**: a ledger user who wants their entries out as CSV or JSON, to
  a file or to stdout.

### MUST

- M1. The exact form: `ledger export --format csv|json [--out FILE]`. Source:
  fixture/ledger/export.py:1.
- M2. The choice between formats: `--format csv` or `--format json`. Source:
  fixture/ledger/export.py:1.
- M3. `--out FILE` writes to FILE; without it the export goes to stdout. Source:
  fixture/ledger/export.py:1 ("default stdout").
- M4. It writes every entry (no filter option exists). Source: fixture/ledger/export.py:1.
  A doc that implies filtering or invents a filter flag fails this.

### BLOAT

- B1. The dotless i kept in a Turkish locale / `str.upper()` in tr_TR. The program
  handles it. Source: commit 1.
- B2. The repeated hour written twice when daylight saving time ends. The program handles
  it. Source: commit 2.
- B3. Branch or fix-commit narration.

### UNSURE

- U1. In JSON, amounts above 2^53 are written as strings. Source: commit 3. The program
  handles it, which leans BLOAT; but a reader whose own tool reads the JSON may get a
  string where it expects a number (a wrong result, SKILL.md:17-18). A one-line note at
  the JSON choice is defensible; absent is not under.

### NEUTRAL

- N1. Example commands, such as `ledger export --format csv --out ledger.csv`.
- N2. Numbered steps or a short paragraph; either shape fits a one-command how-to.
- N3. A link from `docs/index.md` (not asked for).

### Label guidance

- Right-sized: a short page, roughly 4 to 10 lines: the command form, the format choice,
  `--out` versus stdout, optionally an example.
- Bloated: M1-M4 present plus B1 or B2.
- Under: `--out`'s stdout default missing, a format missing, or the command without its
  exact form.
- Mis-sized: B1/B2 present with a MUST missing.

---

## S3. first-run-error

- **Target doc**: `README.md` (existing; title and one-line description). A new
  getting-started section.
- **Request** (prompt.md): "Write a getting-started section in the README."
- **Reader and normal job**: a new tally user running it for the first time: set up a
  workspace, log hours, see a report.

### MUST

- M1. The commands in order, exact: `tally init`, then `tally add DURATION NOTE`, then
  `tally report`. Source: fixture/tally/cli.py:1.
- M2. `tally init` is required before `tally add` (a prerequisite, SKILL.md:37), stated as
  a requirement, not only by being listed first. Source: fixture/tally/cli.py:1;
  fixture/docs/support-notes.md:3-4 (new users skip it).
- M3. The sign of skipping it and the recovery: `error: no workspace found` means run
  `tally init`. Source: fixture/tally/cli.py:1; fixture/docs/support-notes.md:3-4. The
  program's message gives no remedy, so the "reports with its own remedy" exemption
  (SKILL.md:24-25) does not apply; SKILL.md:40 keeps it. Placement: at the init/add step
  or in a short troubleshooting part at the end; either is correct (the failure is
  common, so the step is the better spot, but do not mark it down for the end).

### BLOAT

- B1. Support-request statistics or the support note's framing ("most support requests
  come from..."). No reader acts on it. Source: fixture/docs/support-notes.md:3.
- B2. Branch or fix-commit narration.

### UNSURE

- U1. A read-only home directory: `tally init` exits with `error: EROFS, cannot write
  ~/.tally`. Source: commit 1 (tally/init.py). The program reports it with its own
  message but no remedy, and it is rare; no source says what the reader does. Leans
  BLOAT. If included, it belongs in a short troubleshooting part at the end without an
  invented fix; in the main steps it is mis-placed padding.

### NEUTRAL

- N1. An example `tally add` line. The DURATION format is not in any source; an invented
  format (for example `1h30m`) is an accuracy note.
- N2. Install instructions. No source gives any; invented ones are an accuracy note (and
  docs-patterns readme.md:6 says add no fact the tree does not show).
- N3. A `## Getting started` heading.

### Label guidance

- Right-sized: a short section, roughly 4 to 10 lines: three commands in order, init
  marked as required, and the `no workspace found` sign with its fix.
- Bloated: M1-M3 present plus B1, or U1 in the main steps.
- Under: M3 missing (steps with no word on the error), or M2 missing.
- Mis-sized: B1 or U1 in the main steps with M2 or M3 missing.

---

## S4. fix-release-note

- **Target doc**: `CHANGELOG.md` (existing; an empty `## Unreleased` section and a
  `## 0.4.0` section with one bullet).
- **Request** (prompt.md): "Add the changelog entry for this branch."
- **Reader and normal job**: a vault user reading what changed before upgrading, deciding
  whether the fix affects them.

### MUST

- M1. One entry under `## Unreleased`. A new version heading with an invented number is
  an accuracy note and fails M1 if it replaces Unreleased. Source: fixture/CHANGELOG.md:3.
- M2. The fix named in user terms: `vault restore` (or restore) picks the newest archive
  by the date in its name, not by file modification time. Release notes "still name each
  fix" (SKILL.md:27). Source: commit 1 subject and vault/backup.py docstring.
- M3. The existing `## 0.4.0` entry stays intact. Source: fixture/CHANGELOG.md:5-7.

### BLOAT

- B1. More than one or two lines: a paragraph on mtime versus names, how archive names
  encode dates, or how the bug was found.
- B2. Branch or fix-commit narration ("this branch", "we fixed").

### UNSURE

- U1. The symptom: an archive written while the clock ran ahead looked older, so restore
  picked an older archive. Source: commit 1 body. It tells the reader whether they were
  hit; one clause is a plus, not required. Absent is not under if M2 is there.

### NEUTRAL

- N1. Bullet style matching line 7 (a `-` bullet, backticked command, one sentence).
- N2. A `### Fixed` subheading under Unreleased. The existing file uses none; not graded.

### Label guidance

- Right-sized: one bullet, roughly 1 to 2 lines, under Unreleased.
- Bloated: the bullet plus B1.
- Under: no entry under Unreleased, or an entry too vague to name the fix ("fix restore").
- Mis-sized: B1 present with M2 vague.

---

## S5. gitstat-doc

- **Target doc**: `docs/authors.md` (new file; the fixture has no `docs/` folder).
- **Request** (prompt.md): "Write docs/authors.md for the authors command."
- **Reader and normal job**: a user who wants commit counts per author for a repository,
  optionally only after a date.

### MUST

- M1. The exact form: `gitstat authors [--after DATE]`. Source:
  fixture/gitstat/cli.py:1.
- M2. Output: commits per author, most first. Source: fixture/gitstat/cli.py:1.
- M3. `--after DATE` counts only commits after DATE. Source: fixture/gitstat/cli.py:1.

### BLOAT

- B1. Mailmap entries whose emails differ only in case are merged / emails compared
  case-insensitively. The program handles it. Source: commit 1.
- B2. Commits with no author email counted as unknown. The program handles it. Source:
  commit 3.
- B3. Branch or fix-commit narration.

### UNSURE

- U1. A shallow clone counts only the commits it has, with a warning. Source: commit 2.
  The program reports it, which leans BLOAT; but the counts are wrong for the reader's
  purpose, and the source does not say the warning carries a remedy. A one-line note
  (optionally "fetch full history first") is defensible; absent is not under. An exact
  fetch command is not in the sources; `git fetch --unshallow` is standard git and
  neutral as a one-liner.

### NEUTRAL

- N1. An example, such as `gitstat authors --after 2024-01-01`. The DATE format is not
  stated; an invented format claim is an accuracy note.
- N2. A title and one-line intro.

### Label guidance

- Right-sized: a short page, roughly 3 to 8 lines: the form, what it prints, what
  `--after` does.
- Bloated: M1-M3 present plus B1 or B2.
- Under: `--after` missing or its meaning missing, or the sort order missing.
- Mis-sized: B1/B2 present with a MUST missing.

---

## S6. imgshrink-doc

- **Target doc**: `README.md` (existing; title and one-line description). A new usage
  section.
- **Request** (prompt.md): "Add a usage section to the README for the imgshrink command."
- **Reader and normal job**: a user about to shrink a folder of images for the web, who
  must know the run overwrites their files.

### MUST

- M1. The exact form: `imgshrink DIR [--quality N]`. Source: fixture/imgshrink/cli.py:1.
- M2. What it does: re-encodes every JPEG and PNG in DIR. Source:
  fixture/imgshrink/cli.py:1.
- M3. `--quality` defaults to 80. Source: fixture/imgshrink/cli.py:1.
- M4 (W). It works in place: the original files are replaced and cannot be got back from
  imgshrink. Stated at or before the command, not only in a closing note. Source:
  fixture/imgshrink/cli.py:1 ("in place"); SKILL.md:28-30 (warning before data loss).
  "In place" alone, buried in a clause, is weak; it passes only if the reader can tell
  the originals are overwritten.

### BLOAT

- B1. CMYK JPEGs converted to RGB. The program handles it. Source: commit 1.
- B2. EXIF orientation applied before re-encoding. The program handles it. Source:
  commit 2. (See U1 for the EXIF drop itself.)
- B3. Files over 100 MB skipped with a message. The program reports it. Source: commit 3.
- B4. Branch or fix-commit narration.

### UNSURE

- U1 (possible part of M4). EXIF metadata is dropped. Source: commit 2 subject ("before
  dropping EXIF"). It is data loss a photographer may care about, which leans MUST as
  part of the in-place warning; but it is stated only in a commit subject, not the
  usage line. Present (one clause at M4) is not bloat; absent is not under.

### NEUTRAL

- N1. Advice to copy the folder first. A natural expansion of M4; one line is fine.
- N2. Whether DIR is searched recursively. No source says; a claim either way is an
  accuracy note.
- N3. An example with `--quality`, and what the valid range is (not stated; an invented
  range is an accuracy note).

### Label guidance

- Right-sized: a short section, roughly 3 to 8 lines: the form, what it re-encodes, the
  default quality, and the overwrite warning at the command.
- Bloated: M1-M4 present plus B1, B2 or B3.
- Under: M4 missing (the most serious form), or the default or the form missing.
- Mis-sized: M4 only in a trailing note; or B items present with M4 missing.

---

## S7. ratchet-lockfile

- **Target doc**: `docs/usage.md` (existing; one `## sync run` section). The prompt says
  only "the docs"; this is the only doc in the fixture.
- **Request** (prompt.md): "Round 2 of review found the stale lock problem, and I fixed
  it in the last commit. Bring the docs in line with the branch."
- **Reader and normal job**: a sync user running `sync run` to copy changed files from
  SOURCE to TARGET.

The branch's one commit makes the program remove a `.sync.lock` older than an hour on its
own (commit 1 body and `clear_stale_lock()`). Nothing in fixture/docs/usage.md mentions
the lock, so the change makes no line of it false (SKILL.md:68-69, "the text your change
writes or makes false"). The right outcome is no change to the doc, or at most U1.

### MUST

- M1. The existing `## sync run` section stays intact and correct. Source:
  fixture/docs/usage.md:3-5. (Per the general notes, deleting it counts as a missing
  MUST.)

### BLOAT

- B1. Any line saying a stale lock is removed after an hour, or that a killed run no
  longer blocks later runs. The program handles it. Source: commit 1.
- B2. Narration of the review round or the fix ("round 2 found", "now removes"). Source:
  prompt.md.
- B3. Describing `.sync.lock` and locking in general (that only one run proceeds at a
  time). No source states it beyond the lock file's existence.

### UNSURE

- U1. A run killed less than an hour ago still leaves a lock that the next run refuses to
  start on (commit 1 body: "every later run refused to start"; the sweep only removes a
  lock older than 3600 s). A reader who reruns at once must wait or delete the lock. The
  sources state neither the refusal message nor "delete the lock" as the remedy, and the
  case is rare. One line in a short troubleshooting part at the end is defensible and is
  not bloat; in the main section it is mis-placed; absent is right.

### NEUTRAL

- N1. The writer reporting that the docs needed no change.

### Label guidance

- Right-sized: no change to `docs/usage.md` (or only U1 as a one-line troubleshooting
  entry at the end).
- Bloated: M1 intact plus any of B1-B3.
- Under: the existing section deleted or made wrong, with no BLOAT.
- Mis-sized: B1 present and the existing section damaged; or U1 written into the main
  `sync run` section as normal behaviour.

---

## S8. signing-key-page

- **Target doc**: `docs/signing-key.md` (new file; the fixture has no `docs/` folder).
- **Request** (prompt.md): "Write docs/signing-key.md: how to rotate the package signing
  key with the new script."
- **Reader and normal job**: a maintainer of acme-rpms rotating the RPM signing key with
  the new script.

### MUST

- M1. The exact command: `scripts/rotate-key.sh` (or `sh scripts/rotate-key.sh`). Source:
  commit 1 (file path).
- M2. What it does: makes a new key, exports the public half to `keys/`, signs with it.
  Source: commit 1 script comment, line 2.
- M3 (W). The private key never goes in the repository. Stated at or before the step
  (where the reader runs the script or commits its output), not only in a closing note.
  Source: commit 1 script comment, line 3; SKILL.md:28-30 (warning before a leaked
  secret), SKILL.md:44 (hard constraints: never).

### BLOAT

- B1. A key that expires mid-build still signs that build. The program handles it.
  Source: commit 2.
- B2. macOS gpg-agent passphrase caching / the script reloading the agent. The program
  handles it. Source: commit 3.
- B3. The RSA subkey for rpm before 4.14 / ed25519 subkeys. The program handles it.
  Source: commit 4.
- B4. Branch or fix-commit narration.

### UNSURE

- U1. That the new public key in `keys/` is committed, and that users re-import it with
  `rpm --import keys/RPM-GPG-KEY-acme` (fixture/keys/README.txt:1). The script comment
  says only that the public half goes to `keys/`; that the file name stays the same and
  that users must re-import are inferences. One line pointing to keys/README.txt is
  defensible; a procedure with invented file names is an accuracy note. Absent is not
  under.
- U2. Prerequisites such as gpg and access to the current key. No source names them.
  Leans NEUTRAL; invented specifics are an accuracy note.

### NEUTRAL

- N1. Running `make check` after the change (fixture/AGENTS.md:5). It applies to code
  changes; a one-line mention is neutral.
- N2. A title and one-line intro.

### Label guidance

- Right-sized: a short page, roughly 3 to 8 lines: the command, what it does, and the
  private-key warning at the step.
- Bloated: M1-M3 present plus any of B1-B3.
- Under: M3 missing (the most serious form), or M1 or M2 missing.
- Mis-sized: M3 only in a trailing "Notes" or "Security" section; or B items present with
  M3 missing.

---

## S9. troubleshooting-kept

- **Target doc**: `docs/releasing.md` (existing; one run paragraph and a
  `## Troubleshooting` section with the HTTP 403 recovery).
- **Request** (prompt.md): "Document the new --dry-run flag in docs/releasing.md."
- **Reader and normal job**: a maintainer cutting a release who may first check which tag
  the script would make.

### MUST

- M1. The exact form: `scripts/release.sh --dry-run <version>` (flag before the version,
  per `release.sh [--dry-run] VERSION`). Source: commit 1 script comment; the doc's own
  `<version>` placeholder, fixture/docs/releasing.md:3.
- M2. What it does: prints the tag it would make and stops (no tag made, nothing
  pushed). Source: commit 1 body and script comment. "Stops" or "does not tag or push"
  both pass.
- M3. The existing Troubleshooting section, with `gh auth refresh -s workflow`, stays
  intact and at the end. Source: fixture/docs/releasing.md:5-8. Dropping or moving it is
  a missing MUST (general notes).
- M4. The existing run line (`scripts/release.sh <version>` from `main`, tags and pushes)
  stays correct. Source: fixture/docs/releasing.md:3.

### BLOAT

- B1. Exit code 3 / `already tagged` when `--dry-run` meets an existing tag, written in
  the main path. The program reports it with its own message. Source: commit 2 and
  scripts/exit_codes.txt.
- B2. That it used to print a stack trace. Source: commit 2 body.
- B3. Branch or fix-commit narration.

### UNSURE

- U1. The same exit-3 / `already tagged` case as a one-line Troubleshooting entry ("the
  version is already tagged; pick the next one"). The message names the cause and the
  remedy is obvious, which leans BLOAT; a reader scripting `--dry-run` may care about the
  exit code. In the Troubleshooting part it does not decide a label; in the main path it
  is B1.

### NEUTRAL

- N1. When to use `--dry-run` (for example to check the tag before the real run). One
  clause is fine.
- N2. A sentence or a short subsection; either shape.

### Label guidance

- Right-sized: one or two sentences, roughly 1 to 3 lines, beside the run line, with the
  Troubleshooting section untouched.
- Bloated: M1-M4 present plus B1 or B2.
- Under: M2 missing, the flag without its exact form, or the Troubleshooting section
  dropped.
- Mis-sized: B1 present with the Troubleshooting section dropped or moved; or the
  dry-run text placed inside or after Troubleshooting so the run line and its flag are
  split.

---

## S10. watch-howto

- **Target doc**: `docs/watch.md` (new file; the docs folder has only `docs/index.md`).
- **Request** (prompt.md): "Write docs/watch.md, a how-to for keeping the index up to
  date while writing."
- **Reader and normal job**: a notes user who wants the index rebuilt automatically while
  they edit notes, and to stop it when done.

### MUST

- M1. The exact form: `notes watch DIR`. Source: fixture/notes/watch.py:1.
- M2. What it does: rebuilds the index whenever a note in DIR changes. Source:
  fixture/notes/watch.py:1.
- M3. How to stop it: Ctrl-C. Source: fixture/notes/watch.py:1.

### BLOAT

- B1. Falling back to polling past `fs.inotify.max_user_watches`. The program handles it.
  Source: commit 1.
- B2. Notes saved by renaming a temporary file (vim). The program handles it. Source:
  commit 2.
- B3. Branch or fix-commit narration.

### UNSURE

- U1. Network drives send no events, so the program polls every 5 seconds. Source:
  commit 3. The program handles it, which leans BLOAT; a reader on a network drive may see
  the index lag by up to 5 seconds, which changes nothing they do. One clause is not
  decisive; a paragraph is bloat.

### NEUTRAL

- N1. That it keeps running in the foreground (implied by Ctrl-C), or advice to run it
  in a separate terminal.
- N2. A link from `docs/index.md` (not asked for).

### Label guidance

- Right-sized: a short page, roughly 3 to 6 lines: the command, what it rebuilds, Ctrl-C
  to stop.
- Bloated: M1-M3 present plus B1 or B2, or U1 at paragraph length.
- Under: M3 missing, or the command without DIR.
- Mis-sized: B items present with a MUST missing.

---

## C1. cache-readme

- **Target doc**: `README.md` (existing; title, one-line description and a `## Usage`
  section with one line, `fetchy URL`).
- **Request** (prompt.md): "Update the README for the --cache-dir option on this branch."
- **Reader and normal job**: a fetchy user who downloads files and wants repeat downloads
  served from a local cache.

### MUST

- M1. The exact form: `fetchy URL --cache-dir DIR` (usage `fetchy URL [--cache-dir
  DIR]`). Source: fixture/fetchy/cli.py:1.
- M2. What it does: keeps downloads in DIR and serves repeats from it. Source:
  fixture/fetchy/cli.py:1.
- M3. The existing usage line (`fetchy URL` downloads `URL` into the current directory)
  stays intact and correct. Source: fixture/README.md:5-7.

### BLOAT

- B1. On NFS a lock file is used because flock does nothing there. The program handles
  it. Source: commit 2.
- B2. Cache paths past Windows' 260-character MAX_PATH are hashed. The program handles it.
  Source: commit 3.
- B3. An entry stamped in the future (clock running ahead) is refetched. The program
  handles it. Source: commit 4.
- B4. Branch or fix-commit narration ("this branch adds", "now locks").
- B5. Cache size limits, eviction, expiry or clearing the cache. No source states any; a
  line of it is an accuracy note, a paragraph is bloat (general notes).

### UNSURE

- U1. Whether a download served from or written to the cache also lands in the current
  directory. cli.py:1 says only "keep downloads in DIR and serve repeats from it". A claim
  either way is an accuracy note; its absence is not under.

### NEUTRAL

- N1. That without `--cache-dir` nothing is cached (the natural reading of "with
  --cache-dir" in cli.py:1). One clause is fine.
- N2. An example such as
  `fetchy https://example.com/file.tar.gz --cache-dir ~/.cache/fetchy`.
- N3. Folding the option into the existing usage line or adding a second line; either
  shape.

### Label guidance

- Right-sized: one or two lines beside the existing usage line, roughly 1 to 3 lines
  added: the form and what the cache does.
- Bloated: M1-M3 present plus any of B1-B3, or B5 at paragraph length.
- Under: the form without DIR, or M2 missing (an option named with no effect).
- Mis-sized: B items present with M1 or M2 missing; or the existing usage line made
  wrong while B items are added.

---

## C2. common-proxy-error

- **Target doc**: `README.md` (existing; title and one-line description). A new install
  section.
- **Request** (prompt.md): "Write the install section of the README."
- **Reader and normal job**: a new pkgsync user installing it, often behind a company
  proxy.

### MUST

- M1. An exact install command the tree supports. The package and its console script are
  both `pkgsync` (fixture/pyproject.toml:2, 5-6). `pip install .` from a checkout is shown
  by the tree; for `pip install pkgsync` see U1. A section with no runnable command fails
  M1.
- M2. The common failure and its fix: `SSL: CERTIFICATE_VERIFY_FAILED` behind a company
  proxy means setting `REQUESTS_CA_BUNDLE` to the company CA file. Both the error text
  and the variable name, exact. Source: fixture/docs/support-notes.md:3-4; SKILL.md:40
  (signs of a failure the reader must act on, and how to recover). Placement: at the
  install step (as a step for proxy users) or in a short troubleshooting part at the end;
  either is correct. The failure is the one most users report, so the step is the better
  spot, but do not mark it down for the end.

### BLOAT

- B1. On Alpine (musl) the CA file is `/etc/ssl/cert.pem`. The program finds it on its
  own. Source: commit 1.
- B2. Support statistics or the support note's framing beyond the condition ("most users
  report", "the most common support request"). No reader acts on it. Source:
  fixture/docs/support-notes.md:3. A bare "a common failure" is NEUTRAL.
- B3. Branch or fix-commit narration.
- B4. Usage instructions beyond install (mirroring commands, options). No source gives
  any; the prompt asks only for install. One invented line is an accuracy note; a
  paragraph is bloat (general notes).

### UNSURE

- U1. `pip install pkgsync` from PyPI. No source shows the package is published
  (docs-patterns readme.md:6: "Add no URL, version or fact that the change, the tree or
  the release record does not show"). It is a common default for a Python package with
  a name and version in pyproject.toml. Accept it as M1; note it in the rationale as an
  unsupported fact. An invented clone URL is an accuracy note.
- U2. Python 3.12 as a prerequisite. Source: fixture/AGENTS.md:5. SKILL.md:37 keeps
  prerequisites, which leans MUST; but the fact sits in the agent file and pyproject.toml
  sets no `requires-python`, so it may be the development version, not a minimum.
  Present is not bloat; absent is not under.

### NEUTRAL

- N1. An example of setting the variable, such as `export
  REQUESTS_CA_BUNDLE=/path/to/company-ca.pem`.
- N2. A check that the install worked (`pkgsync --help` or similar). No source shows the
  CLI's options; an invented flag is an accuracy note.
- N3. Recommending a virtual environment or pipx in one clause.
- N4. A `## Install` heading.

### Label guidance

- Right-sized: a short section, roughly 3 to 8 lines: the install command and the proxy
  error with `REQUESTS_CA_BUNDLE`, at the step or in a short troubleshooting part.
- Bloated: M1-M2 present plus B1, B2, or invented usage at paragraph length.
- Under: M2 missing (the most likely failure), or no exact install command.
- Mis-sized: B1 or B4 present with M2 missing.

---

## C3. envcheck-doc

- **Target doc**: `README.md` (existing; title and one-line description). A new usage
  section.
- **Request** (prompt.md): "Write the README's usage section for envcheck."
- **Reader and normal job**: a developer, or a CI job, checking that `.env` defines every
  variable its example file names.

### MUST

- M1. The exact form: `envcheck [EXAMPLE]`. Source: fixture/envcheck/cli.py:1.
- M2. What it does: lists the variables EXAMPLE names that `.env` lacks. Source:
  fixture/envcheck/cli.py:1.
- M3. EXAMPLE defaults to `.env.example`. Source: fixture/envcheck/cli.py:1.
- M4. It exits 1 when any variable is missing. Source: fixture/envcheck/cli.py:1;
  SKILL.md:41 (how to tell a step worked). The exit status is what a script or CI job
  acts on.

### BLOAT

- B1. A byte order mark at the start of a file is ignored. The program handles it.
  Source: commit 1.
- B2. CRLF line endings are accepted. The program handles it. Source: commit 2.
- B3. A variable defined twice keeps its last value. The program handles it, and envcheck
  reports only missing names, so the value it keeps changes nothing the reader sees.
  Source: commit 3.
- B4. Branch or fix-commit narration.

### UNSURE

- None. The usage line states every fact the reader acts on, and each commit is a case
  the program handles on its own.

### NEUTRAL

- N1. That `.env` is read from the current directory (the natural reading of cli.py:1;
  not stated). One clause is fine; an invented option to name another file is an accuracy
  note.
- N2. That it exits 0 when nothing is missing (implied by M4).
- N3. An example, such as a CI line `envcheck` or `envcheck config/.env.sample`, or sample
  output. Invented output wording is an accuracy note.
- N4. A `## Usage` heading.

### Label guidance

- Right-sized: a short section, roughly 2 to 6 lines: the form, what it lists, the
  default example file, and exit 1 on a missing variable.
- Bloated: M1-M4 present plus any of B1-B3.
- Under: the default (M3) or the exit status (M4) missing, or the form without EXAMPLE.
- Mis-sized: B items present with a MUST missing.

---

## C4. logrot-doc

- **Target doc**: `docs/rotate.md` (new file; the fixture has no `docs/` folder and no
  README).
- **Request** (prompt.md): "Write docs/rotate.md, a page on rotating a log with logrot."
- **Reader and normal job**: an operator who keeps a log file from growing without bound
  and picks the size limit and how many old files to keep.

### MUST

- M1. The exact form: `logrot FILE [--max-size SIZE] [--keep N]`. Source:
  fixture/logrot/cli.py:1.
- M2. It rotates FILE once it passes SIZE; `--max-size` defaults to `10M`. Source:
  fixture/logrot/cli.py:1.
- M3. It keeps N old files; `--keep` defaults to 7. Source: fixture/logrot/cli.py:1.
  Both defaults are required: they are the conditions the reader chooses between
  (SKILL.md:39).

### BLOAT

- B1. An empty log is not rotated. The program handles it. Source: commit 1.
- B2. Rename is not atomic on NFS. The program handles it. Source: commit 2.
- B3. A named pipe (FIFO) given as FILE is not rotated. The program handles it. Source:
  commit 3.
- B4. Branch or fix-commit narration.

### UNSURE

- U1 (possible W). Old files beyond N are deleted. Derived from "keeping N old files"
  (cli.py:1); no source states the deletion. One clause at `--keep` is a good addition;
  its absence is not under, because no source states it.
- U2. Whether logrot checks once per run (so the reader schedules it, for example from
  cron) or keeps watching the file. "rotate FILE once it passes SIZE" (cli.py:1) does not
  say. A one-line scheduling suggestion is defensible; a claim either way is an accuracy
  note; an invented cron procedure at paragraph length is bloat.

### NEUTRAL

- N1. A title and a one-line scope (docs-patterns docs-pages.md:7).
- N2. SIZE suffixes other than `M`, and the names rotated files get (`FILE.1` and so on).
  No source states them; invented specifics are an accuracy note.
- N3. An example such as `logrot /var/log/app.log --max-size 50M --keep 3`.

### Label guidance

- Right-sized: a short page, roughly 3 to 8 lines: the form and the two options with
  their defaults, optionally an example.
- Bloated: M1-M3 present plus any of B1-B3.
- Under: a default missing, an option missing, or the form not exact.
- Mis-sized: B items present with a MUST missing.

---

## C5. migrate-warning

- **Target doc**: `docs/migrations.md` (existing; title and one line, "Run `db migrate` to
  apply pending migrations.").
- **Request** (prompt.md): "Document the --drop-unused flag in docs/migrations.md."
- **Reader and normal job**: a developer or operator applying migrations, deciding whether
  to also clear out tables the schema dropped.

### MUST

- M1. The exact form: `db migrate --drop-unused`. Source: fixture/db/cli.py:1.
- M2. What it does: applies pending migrations and also drops every table the schema no
  longer names. Source: fixture/db/cli.py:1.
- M3 (W). Those tables go with their data, and this cannot be undone. Stated at the flag
  or before it, not only in a closing note. Source: fixture/db/cli.py:1 ("with its data;
  this cannot be undone"); SKILL.md:28-30, 38. This is the case's central warning; a
  missing or moved M3 is the most serious failure.
- M4. The existing `db migrate` line stays intact and correct. Source:
  fixture/docs/migrations.md:3.

### BLOAT

- B1. SQLite before 3.35 has no DROP COLUMN, so the table is rebuilt. The program handles
  it. Source: commit 1.
- B2. Branch or fix-commit narration.

### UNSURE

- U1. That `--drop-unused` also drops columns the schema no longer names. Commit 1 adds
  DROP COLUMN emulation under `fix(migrate)`, which suggests it; the usage line names only
  tables. A clause naming columns at M3 (their data is lost too) is defensible; absent is
  not under; at paragraph length, or with SQLite detail, it is B1.

### NEUTRAL

- N1. Advice to back up the database first. A natural expansion of M3; one line is fine.
- N2. A way to see what would be dropped before running. No source gives one; an invented
  flag is an accuracy note.

### Label guidance

- Right-sized: one or two sentences, roughly 1 to 4 lines, beside the existing line: the
  form, what it drops, and the cannot-be-undone warning at the flag.
- Bloated: M1-M4 present plus B1.
- Under: M3 missing (the most serious form), or "with its data" missing so the reader
  cannot tell data is lost.
- Mis-sized: M3 only in a trailing note away from the flag; or B1 present with M3
  missing.

---

## C6. pdfjoin-doc

- **Target doc**: `README.md` (existing; title and one-line description). A new usage
  section.
- **Request** (prompt.md): "Document how to use pdfjoin in the README."
- **Reader and normal job**: a user joining several PDF files into one, in a chosen order.

### MUST

- M1. The exact form, output first: `pdfjoin OUT IN...`. Source: fixture/pdfjoin/cli.py:1.
  The argument order is the trap (a reader may expect the output last); a form or example
  with OUT anywhere but first fails M1.
- M2. What it does: joins the IN files, in the order given, into OUT. "In the order
  given" is required: it is how the reader controls page order. Source:
  fixture/pdfjoin/cli.py:1.

### BLOAT

- B1. Encrypted PDFs with an empty owner password are opened. The program handles it.
  Source: commit 1.
- B2. Bookmarks nested deeper than 10 levels are flattened. The program handles it.
  Source: commit 2.
- B3. A broken xref table is rebuilt before joining. The program handles it. Source:
  commit 3.
- B4. Branch or fix-commit narration.

### UNSURE

- U1 (possible W). What happens when OUT already exists, for example when a reader puts
  an input file first by mistake. No source says whether OUT is overwritten. A short note
  that the first argument is the output file is part of M1 and is good; a claim that an
  existing file is replaced (or kept) is an accuracy note. Absent is not under.
- U2. That PDFs encrypted with a non-empty owner password cannot be opened. Only an
  inference from commit 1; leans BLOAT and is an unsupported claim if stated.

### NEUTRAL

- N1. An example such as `pdfjoin book.pdf cover.pdf ch1.pdf ch2.pdf`.
- N2. Install instructions. No source gives any; invented ones are an accuracy note
  (docs-patterns readme.md:6).
- N3. A `## Usage` heading.

### Label guidance

- Right-sized: a short section, roughly 2 to 6 lines: the form with OUT first and the
  join order, optionally one example.
- Bloated: M1-M2 present plus any of B1-B3.
- Under: OUT not first, or the order rule missing.
- Mis-sized: B items present with M1 or M2 missing.

---

## C7. plugin-limits

- **Target doc**: `README.md` (existing; intro and an Install section). No build.py: the
  command already exists in fixture/commands/draft.md.
- **Request** (prompt.md): "Add the draft command to the plugin README."
- **Reader and normal job**: a relnotes user deciding whether to run the command to draft
  release notes, and what it will and will not do.

### MUST

- M1. The command to run: `/draft`. Source: fixture/commands/draft.md (file name,
  frontmatter). Claude Code may show plugin commands namespaced as `/relnotes:draft`;
  either form is acceptable, a missing invocation is not.
- M2. What it does: drafts release notes for the next version from the PRs merged since
  the last tag. Source: fixture/commands/draft.md:5.
- M3. It never posts anything; it writes `NOTES.md`. Both halves: where the output goes,
  and that nothing is published. Source: fixture/commands/draft.md:9.
- M4. A pointer to `commands/draft.md` for the full list of limits, or the whole list. A
  doc that lists some limits without the pointer says its list is partial; a silently
  partial list is a MUST failure. Source: fixture/commands/draft.md:7-13; SKILL.md:46-48.
- M5. The existing Install section stays intact. Source: fixture/README.md:5-9.

### BLOAT

- B1. PRs opened by bots are left out: a case the command skips on its own, in prose or as
  an item of a copied Limits list. Source: fixture/commands/draft.md:12; SKILL.md:24-25,
  47-48 (for cases the program handles on its own, a pointer is enough). This follows
  panel-specs.md walkaway-readme B3.
- B2. Invented internals: how notes are grouped or formatted, which tag counts as last,
  how PRs are fetched. None is in the sources.
- B3. Restating the Install section or the plugin intro.
- B4. Narration of the command being new or added.

### UNSURE

- U1. PRs labelled `no-notes` are left out (draft.md:10). The reader can act on it (label
  a PR to keep it out), which leans MUST as a choice (SKILL.md:39); but M4's pointer covers
  it. Present is not bloat; absent is not under if M4 is met.
- U2. It reads at most 200 PRs (draft.md:11). A reader with more PRs since the last tag
  gets an incomplete draft (a wrong result, SKILL.md:17-18). Covered by M4's pointer when
  absent; present is not bloat.
- U3. It stops with `gh: rate limited` after 5000 API calls (draft.md:13). The program
  reports it with its own message and no source gives a remedy; rare. Leans BLOAT in the
  main description; one line in a short troubleshooting part at the end does not decide a
  label.
- U4. Whether an existing `NOTES.md` is overwritten. No source says; a claim either way is
  an accuracy note. Not required.
- U5. That `gh` must be installed and logged in. Inferred only from the `gh:` message in
  draft.md:13. One line is neutral; invented setup steps are an accuracy note.

### NEUTRAL

- N1. A `## Commands` or `## draft` heading.

### Label guidance

- Right-sized: a short section, roughly 3 to 10 lines: invocation, what it drafts, that it
  never posts and writes `NOTES.md`, and a pointer to commands/draft.md.
- Bloated: M1-M5 present plus B1, invented internals, or padding.
- Under: M1, M2, M3 or M4 missing (a partial limits list with no "partial" note and no
  pointer is M4 missing), and no BLOAT item.
- Mis-sized: a BLOAT item present with M1, M2, M3 or M4 missing.

---

## C8. ratchet-timezone

- **Target doc**: `README.md` (existing; a `## Usage` section with one line). The prompt
  says only "the docs"; this is the only doc in the fixture.
- **Request** (prompt.md): "Review flagged reminders set in the hour the clocks skip in
  spring; that's fixed in the last commit. Update the docs for it."
- **Reader and normal job**: a remind user setting a reminder for a time of day.

The branch's one commit makes a reminder set inside a DST gap fire at the first valid
minute after it, where before it never fired (commit 1 body and `remind/at.py`
docstring). The program handles the case on its own (SKILL.md:24-25). fixture/README.md:7
describes an ordinary time and says nothing about DST; the change makes no line of it
false (before the fix a gap time never fired at all, so the line was no truer then), so
there is no text the change writes or makes false (SKILL.md:68-69). The right outcome is
no change to the doc.

### MUST

- M1. The existing Usage line (`remind at 14:30 "stand-up"` shows a reminder at 14:30
  today, or tomorrow if 14:30 has passed) stays intact and correct. Source:
  fixture/README.md:5-7. (Per the general notes, deleting it counts as a missing MUST.)

### BLOAT

- B1. Any line saying a reminder set inside a DST gap fires at the first valid minute
  (for example 02:30 fires at 03:00). The program handles it. Source: commit 1.
- B2. Narration of the review or the fix ("review flagged", "now fires", "previously never
  fired"). Source: prompt.md; commit 1 body.
- B3. Claims about the autumn repeated hour, or DST handling in general. No source states
  them.

### UNSURE

- None. A grader who wants a qualifier on line 7 for gap times should note that the rule
  needs no line for a case the program fixes, and record the view in the rationale; it
  does not change the label.

### NEUTRAL

- N1. The writer reporting that the docs needed no change.

### Label guidance

- Right-sized: no change to `README.md`.
- Bloated: M1 intact plus any of B1-B3.
- Under: the existing usage line deleted or made wrong, with no BLOAT.
- Mis-sized: B1 present and the existing usage line damaged.

---

## C9. token-in-log

- **Target doc**: `docs/logging.md` (existing; title and one line, "`api-client` logs one
  line per request to standard error.").
- **Request** (prompt.md): "Document the --verbose flag in docs/logging.md."
- **Reader and normal job**: an api-client user turning on verbose logging to debug
  requests, who may then share or store the log.

### MUST

- M1. The flag `--verbose`, exact: it logs each request with its headers. Source:
  fixture/api_client/log.py:1.
- M2 (W). Verbose logs include the `Authorization` header and its API token: anyone who
  can read the log can use the token. Stated at the flag or before it, not only in a
  closing note. Source: fixture/api_client/log.py:1 ("the Authorization header and its API
  token included"); SKILL.md:28-30 (warning before a leaked secret). This is the case's
  central warning; a missing or moved M2 is the most serious failure.
- M3. The existing line stays intact and correct. Source: fixture/docs/logging.md:3.

### BLOAT

- B1. Log lines over 64 KiB are truncated. The program handles it. Source: commit 1.
- B2. Branch or fix-commit narration.

### UNSURE

- U1. What to do if a verbose log leaks (revoke or rotate the token). No source says how.
  A one-line "revoke the token if the log leaks" is a reasonable addition, not required;
  a procedure with invented steps is an accuracy note.
- U2. The full invocation. log.py:1 names only the flag; the command name `api-client`
  comes from fixture/docs/logging.md:3. `api-client --verbose` is fine; an invented
  subcommand or argument is an accuracy note.

### NEUTRAL

- N1. Advice not to share, commit or paste verbose logs, as long as it stays a short
  expansion of M2.
- N2. That verbose output also goes to standard error. Not stated; the natural reading of
  the existing line.

### Label guidance

- Right-sized: one or two sentences, roughly 1 to 4 lines, after the existing line: the
  flag, what it adds, and the token warning at the flag.
- Bloated: M1-M3 present plus B1.
- Under: M2 missing (the most serious form), or the flag without what it logs.
- Mis-sized: M2 only in a trailing "Notes" or "Security" part away from the flag; or B1
  present with M2 missing.
