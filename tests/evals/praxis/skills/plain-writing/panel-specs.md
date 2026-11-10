# Grading specs: plain-writing sizing cases (issue 182)

One section per eval case. A grader reads the doc the writer produced (the target file's
final text, or the diff to it), checks it against the items below, and gives one label.
These specs come from each case's prompt.md, fixture/ and build.py, and the rule (the
plain-writing paragraph "Write for what the reader does" and its "Always keep" list). They
were written without seeing any model output or the case keys.

Case paths below are relative to
`tests/evals/praxis/skills/plain-writing/cases/<case>/`. "commit N" means the Nth entry of
the COMMITS list in that case's build.py (the branch the writer worked on).

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
- M4. The whole Limits list, or a pointer to `commands/walkaway.md` for it, or, if only
  some limits are listed, a statement that the list is partial. The five limits are:
  never pushes to main / merges / force-pushes; stops after 8 rounds; does not run on a
  PR from a fork; skips the run when `gh` is logged out; ignores draft PRs older than 30
  days. Source: fixture/commands/walkaway.md lines 7-13. A silently partial list is a
  MUST failure.

### UNSURE (each could be MUST or BLOAT)

- U1. `gh` must be logged in, or the run is skipped. Source: walkaway.md line 12. The rule
  calls "a case it skips" something that needs no line, but this one is a prerequisite
  the reader must meet before leaving, and the reader is away when the skip happens. Leans
  MUST as a prerequisite; graders should not mark under for its absence if M4's pointer
  or full list covers it.
- U2. Stops after 8 rounds (the reader may come back to an unfinished review). Source:
  walkaway.md line 10. Covered by M4 if the full list or a pointer is given.
- U3. Does not run on a PR from a fork. Source: walkaway.md line 11. A condition the
  reader checks; covered by M4.
- U4. Ignores draft PRs older than 30 days. Source: walkaway.md line 13. Rare and the
  reader takes little action; leans NEUTRAL. Listing it as part of the whole list is not
  bloat.

### BLOAT

- B1. Explaining how review rounds work internally, what "clean" means beyond the source,
  or which reviewers run: none of it is in the sources.
- B2. Restating the Install section or the plugin intro.

### NEUTRAL

- N1. A `## Commands` or `## walkaway` heading.
- U5 (reviewer's fix: was NEUTRAL). Copying the whole Limits list verbatim. The rule's
  keep list allows "a whole list, or a pointer to where the whole list is", so it
  satisfies M4; but three of the five limits (fork PRs, `gh` logged out, old drafts) are
  cases the command skips, which the rule says "need no line". So the list alone does not
  decide the label either way; record it as U5. Prose that explains or expands the skip
  cases beyond the list's own one-line items is BLOAT (B3).

### BLOAT (added by the reviewer)

- B3. Explanation of the skip cases beyond a one-line list item each (why forks are
  skipped, what happens to old drafts, what the reader sees when `gh` is logged out).
  Source: the rule, "a case it skips ... needs no line".

### Label guidance

- Right-sized: a short section, roughly 3 to 10 lines: invocation, what it does, the
  never-push/merge/force-push guarantees, and either the full Limits list or a pointer to
  commands/walkaway.md.
- Bloated: M1-M4 present plus invented internals, padding, or B3.
- Under: M1, M2 or M3 missing, or a partial limits list with no "partial" note and no
  pointer.
- Mis-sized: invented internals present with M3 or M4 missing.

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
