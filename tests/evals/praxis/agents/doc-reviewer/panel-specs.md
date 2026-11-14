# Grading specs: doc-reviewer cases (issue 182)

One section per screen and confirm case, and per dev case in suite.toml's `BURNED` (D1-D17),
which were screen cases first. The panel grades held-out cases only, so the other dev cases have
no section. A held-out case added later gets its section before its reports are graded
(suite.toml). A grader reads one doc-reviewer report on the case's branch, checks it against the
items below, and gives one label. These specs come from each case's
`prompt.md`, `fixture/` and `build.py` (its COMMITS list, the branch the reviewer reviews) and
the rule (`plugins/praxis/agents/doc-reviewer.md` and plain-writing's "Write for what the reader
does"). They were written without seeing any model output or the case keys. The dev sections
(D1-D15) are the earlier panel's specs, copied because those cases have not changed since; the
owner's ruling below changed D3, D4 and D11. D16 and D17 are screen specs S9 and S15 as graded,
from before their cases were fixed; each says what its fix changed.

Case paths below are relative to `tests/evals/praxis/agents/doc-reviewer/cases/<case>/`. Line
numbers are of the file at the branch tip (fixture plus all commits); "main" means the fixture
as given; "commit N" is the Nth entry of the COMMITS list.

## Labels

Decide in this order; the first that applies is the label.

1. **misses-error**: the report does not raise an E item or an H item.
2. **over-cuts**: the report rates a K line as Bloat or asks to cut it.
3. **under-cuts**: in a case with a B item, the report raises no B item; or, in any case, it
   asks to add an A item to the doc for people.
4. **right**: none of the above.

UNSURE and NEUTRAL items never decide a label; note them in the rationale. Reports differ in
format, and format never decides a label.

## Rule points

- doc-reviewer Important: "Factually incorrect information", "Unsupported claims", "Broken
  cross-references and dead external links", "Bloat -- passages `plain-writing`'s Cut list names,
  and lines its 'Write for what the reader does' leaves out of a document for people", and
  "Missing critical information ... a case `plain-writing`'s 'Write for what the reader does'
  leaves out of a document for people is no finding".
- doc-reviewer Critical: "Safety-critical docs where a wrong step causes real harm -- a wrong
  migration/rollback (data loss) ... (Ordinary doc-code mismatch is Important.)"
- plain-writing: "What the program handles on its own -- a case it skips, fixes or reports with
  its own remedy -- needs no line"; "a warning before data loss, a leaked secret or a step that
  cannot be undone stays where the reader acts, however rare"; recovery from a failure the
  reader must act on is kept, "with recovery from a rare failure in a short troubleshooting part
  at the end"; scope: "In an existing file, apply these lists ... to the text your change writes
  or makes false".

## Grading conventions

- An E item counts as raised when a finding says the line is wrong or unsupported and names the
  right value or source (or at least the contradiction). Severity does not decide the label;
  record it.
- A B item counts as raised when a finding targets that passage (or one of its sentences) and
  rates it Bloat or asks to cut it, at any severity. Record the severity; the rule asks
  Important.
- An over-cut counts when a finding rates a K line as Bloat or asks to cut it, at any severity,
  including as one option of its fix. Fixing a K line's wrong value (an E item) is not a cut. A
  finding that asks to move a kept line (for example into a troubleshooting part at the end)
  without cutting it is not an over-cut.
- An add-ask (A item) counts only when a finding asks the doc for people to state the handled
  case, at any severity, "consider adding" included. Asking for it in a code comment, docstring,
  commit message or changelog does not count. Asking for a pointer to where the handled cases
  are listed does not count (the rule allows such a pointer). A note that says a case was rightly
  left out does not count.
- Findings outside the doc for people (code that is only comments, commit messages, placement,
  a missing CI gate, orphan pages) never decide a label, at any severity.

## Owner's ruling (2026-11-10)

- An ask to fix a sentence the change made false is a correct ask: allowed, not required. When a
  handled case makes a sentence the branch wrote false (it says "every JPEG" and files over
  100 MB are skipped; it says "local time" and the program falls back to UTC), a finding that
  asks the doc to fix that sentence, by qualifying it or by a sentence beside it, is an F item.
  It is never an add-ask, and not raising it is not misses-error. Record its form: `qualify`
  (changes the sentence) or `separate` (adds a sentence or note of its own).
- A line that explains output the reader sees (an `unknown` row in a listing) is borderline: an
  ask for it decides no label.

The ruling came after the first grading round of D1-D15, which used the earlier text.

---

## Dev cases

### D1. cost-deadlink

- Doc: `README.md`, doc for people. Main had lines 1-3 ("# fetchy" / "Download files with
  retries."). The branch (commit 2 "docs: add usage to the README") appended to line 3 "See
  `[Setup](docs/setup.md)` for proxies." and wrote lines 5-7 "## Usage" / "`fetchy URL` downloads
  `URL`." Commit 1 "fix: stop at the body's end when Content-Length is larger than the body"
  adds `fetchy/body.py` only (docstring "A Content-Length larger than the body ends at the
  body.").
- Reader: a user who wants to download a file.
- E1: `README.md:3` links `docs/setup.md`; no `docs/` directory exists in the fixture or any
  commit (files are only `AGENTS.md`, `CLAUDE.md`, `README.md`, `fetchy/__init__.py`,
  `fetchy/body.py`). Dead internal link -- Important ("Broken cross-references").
- H: none. B: none (no handled case is written into the doc).
- K: "`fetchy URL` downloads `URL`." (the one command); "Download files with retries."
  (stood on main).
- A: the Content-Length case (commit 1). A finding asking the README to say a Content-Length
  larger than the body stops at the body's end -> under-cuts.
- UNSURE: "with retries" (line 3, on main) and "`fetchy URL`" have no source either way
  (`fetchy/__init__.py` is empty, no entry point); a finding calling them unsupported is fine,
  not raising them is fine. A fix that drops the link vs. one that asks to create
  `docs/setup.md` both count as raising E1.
- NEUTRAL: commit-message style, missing docs CI gate, no changelog.
- Right: raises the dead `docs/setup.md` link, asks to add nothing about Content-Length. Common
  wrong: under-cuts by asking to document the Content-Length fix; misses-error by not checking
  the link target.

### D2. bloat-envcheck

- Doc: `README.md`, doc for people. Main had lines 1-3. Branch (commit 4 "docs: document the
  command") wrote lines 5-11 ("## Usage" and two paragraphs).
- Reader: a developer checking their `.env`, possibly gating CI on it.
- E1: `README.md:8` "exits 2 when any are missing" vs `envcheck/cli.py:1` docstring "Exits 1
  when any are missing." Wrong exit code -- Important (factually incorrect).
- H: none.
- B1: `README.md:10-11` "A byte order mark at the start of a file is ignored, and so are CRLF
  line endings. A variable defined twice keeps its last value." Handled by commits 1 "fix
  (envcheck): ignore a byte order mark", 2 "fix(envcheck): accept CRLF line endings", 3 "fix
  (envcheck): keep the last value of a variable defined twice" (code comments `cli.py:2-4`).
  The rule asks Important (Bloat).
- K: "Run `envcheck` in the project. It lists each variable `.env.example` names that `.env`
  lacks, and exits [1] when any are missing" (the command, what it reports, the exit code the
  reader gates on).
- A: none beyond B1's three cases (asking to keep/expand them is the B miss, not a new add).
- UNSURE:
  - `README.md:11` "Keys containing spaces are ignored." has no source at all (no commit, no
    comment). It looks planted as an unsupported claim. A finding calling it unsupported is
    right on that point; cutting it inside B1 is consistent with B1. Not raising it should not
    alone make misses-error (it is not contradicted, only unsupported).
  - "so it can gate CI" (line 8): a short reason; a finding cutting just that clause as filler
    is not clearly an over-cut.
- NEUTRAL: asking to document the optional `[EXAMPLE]` argument (default `.env.example`) from
  the docstring -- an option the reader chooses, not a handled case, so not an under-cut;
  commit messages; changelog.
- Right: exit code 2 -> 1, plus Bloat on lines 10-11. Common wrong: under-cuts (no Bloat
  finding, or only a wording nit on lines 10-11); misses-error (exit code not checked).

### D3. lean-imgshrink

- Doc: `README.md`, doc for people. Main had lines 1-3. Branch (commit 4) wrote lines 5-8.
- Reader: a user shrinking a folder of images.
- E1: `README.md:8` "it defaults to 75" vs `imgshrink/cli.py:1` "--quality defaults to 80."
  Wrong default -- Important.
- H: none firm (see UNSURE).
- B: none (the branch wrote no handled case).
- K: "`imgshrink photos/` re-encodes every JPEG and PNG in `photos/` in place." (command, and
  "in place" is the only hint that originals are overwritten); "`--quality N` sets the JPEG
  quality" (the option).
- F1 (owner ruling 2026-11-10, after grading): files over 100 MB are skipped with a message
  (commit 3), so the K sentence "re-encodes every JPEG and PNG" is false for them. A finding
  asking the README to state the limit -- qualifying "every" (for example "up to 100 MB") or a
  sentence beside it saying larger files are skipped -- is right, not an add-ask. Not raising
  it is not misses-error. Record its form: `qualify` (changes the "every" sentence) or
  `separate` (adds a sentence or note of its own).
- A: CMYK JPEGs converted to RGB (commit 1); EXIF orientation applied before dropping EXIF
  (commit 2). Asking the README to add either -> under-cuts.
- UNSURE:
  - Re-encoding in place overwrites the originals lossily and no source offers a way back. A
    finding asking for a warning before the command ("back up first; originals are
    overwritten") is defensible and is neither over- nor under-cut; no source calls it
    irreversible and the doc already says "in place", so not raising it is not misses-error.
  - "sets the JPEG quality": the docstring does not say what `--quality` applies to; a finding
    calling "JPEG" unsupported is fine either way.
- NEUTRAL: commit messages, changelog, no docs CI gate.
- Right: raises 75 -> 80 and asks to add neither CMYK nor EXIF handling; asking for F1 is fine.
  Common wrong: under-cuts by asking to document the CMYK or EXIF handling.

### D4. lean-cronlite

- Doc: new file `docs/schedule.md` (commit 4), docs page for people (a how-to); every line is
  branch-written. There is no README or index in the fixture.
- Reader: a user scheduling a job.
- E1: `docs/schedule.md:4` "`cronlite rm ID` removes one" vs `cronlite/cli.py:1` "cronlite
  remove ID". Wrong subcommand -- Important.
- H: none. B: none.
- K: the `cronlite add "0 9 * * 1" ./report.sh` example; "the schedule is a five-field cron
  expression in local time" (matches docstring); "`cronlite list` shows each job with its ID".
- F1 (owner ruling 2026-11-10, after grading): without `/etc/localtime` the program uses UTC,
  silently (commit 2 "fix(cronlite): fall back to UTC without /etc/localtime", comment "No
  /etc/localtime (slim containers): UTC."), so the K sentence "in local time" is false there. A
  finding asking the doc to state the UTC fallback -- in that sentence or beside it -- is right,
  not an add-ask. Not raising it is not misses-error. Record its form: `qualify` (changes the
  "local time" sentence) or `separate` (adds a sentence, note or section of its own).
- A: a run still going at its next start is skipped (commit 1); February 29 schedules run only
  in leap years (commit 3). Asking to add either -> under-cuts.
- UNSURE:
  - "with its ID" is not in the docstring (implied by `remove ID`); a finding on it is fine.
- NEUTRAL: orphan page / no README or nav linking it (asking to add a README or index is not a
  handled case); commit messages.
- Right: raises `rm` -> `remove`, asks to add neither the overlap skip nor Feb 29; asking for
  F1 is fine. Common wrong: misses-error (the subcommand not checked); under-cuts asking for the
  overlap skip or Feb 29.

### D5. lean-limits

- Docs: `README.md` (doc for people; main had lines 1-9, branch commit 2 wrote lines 11-15
  "## Commands" item) and new `commands/walkaway.md` (commit 1; a Claude Code command file --
  the instructions the command runs, so its lines are behaviour, not a doc for people).
- Reader: a plugin user deciding whether to run `/autopilot:walkaway` before stepping away.
- E1: `README.md:14` "stops after 5 rounds" vs `commands/walkaway.md:10` "Stops after 8
  rounds." Wrong limit -- Important.
- H: none.
- B: none (the README carries only the main limits plus a pointer).
- K:
  - `README.md:13-14` "runs review rounds on the current PR until two come back clean. It never
    merges, never pushes to `main` and stops after [8] rounds." (guarantees the reader relies
    on before walking away).
  - `README.md:15` "See `commands/walkaway.md` for all its limits." (the pointer the rule allows
    for a partial list; it says the list is partial).
  - Every line of `commands/walkaway.md`, including the Limits list lines 9-13 ("Never pushes to
    `main`, never merges and never force-pushes." / "Stops after 8 rounds." / "Does not run on a
    PR from a fork." / "Skips the run when `gh` is logged out." / "Ignores draft PRs older than
    30 days."): they define what the command does; asking to cut them -> over-cuts.
  - Install block (main).
- A: in the README, the fork case, the `gh` logged-out skip, and drafts older than 30 days
  (`commands/walkaway.md:11-13`). Asking the README to list them -> under-cuts.
- UNSURE: asking the README to add "never force-pushes" -- a guarantee, not a handled case; the
  pointer covers it. Do not label on it.
- NEUTRAL: frontmatter description wording, commit messages, changelog/version, `make check`.
- Right: raises 5 -> 8 and nothing more substantive. Common wrong: under-cuts asking to inline
  the fork / `gh` / draft limits; over-cuts calling the pointer or the command file's limits
  bloat.

### D6. bloat-walkaway

- Docs: `README.md` (doc for people; main lines 1-9; branch commit 2 wrote lines 11-16) and new
  `commands/walkaway.md` (commit 1, command file, same text as D5).
- Reader: as D5.
- E1: `README.md:14` "stops after 5 rounds" vs `commands/walkaway.md:10` "Stops after 8
  rounds." -- Important.
- H: none.
- B1: `README.md:15-16` "It does not run on a PR from a fork, skips the run when `gh` is logged
  out, and ignores draft PRs older than 30 days." Cases the command skips on its own, defined in
  `commands/walkaway.md:11-13` (commit 1 "feat: add /autopilot:walkaway"). Rule asks Important.
  A suggested replacement pointer to `commands/walkaway.md` is fine.
- K: `README.md:13-14` "runs review rounds on the current PR until two come back clean. It never
  merges, never pushes to `main` and stops after [8] rounds."; every line of
  `commands/walkaway.md` (cutting its Limits lines -> over-cuts); Install block.
- A: none beyond B1.
- UNSURE:
  - A reader whose PR is from a fork might plan around "does not run on a PR from a fork"; the
    rule still names a skip as handled. A Bloat finding that keeps the fork sentence but cuts
    the other two still counts as raising B1.
  - Asking to add "never force-pushes": as D5, do not label on it.
- NEUTRAL: frontmatter, commit messages, changelog/version.
- Right: raises 5 -> 8 and Bloat on lines 15-16. Common wrong: under-cuts (no Bloat finding on
  15-16, or a pointer suggestion that keeps the sentences); over-cuts flagging line 13-14's
  guarantees.

### D7. harm-mirror

- Doc: `docs/sync.md`, docs page for people. Main had lines 1-3. Branch (commit 3 "docs:
  document --mirror") wrote line 5 "Add `--mirror` to make your local bookmarks match the
  server's exactly."
- Reader: a user syncing bookmarks who may choose `--mirror`.
- E: none firm ("match the server's exactly" is true, only incomplete -- the gap is H1).
- H1: `docs/sync.md:5` gives no warning, yet `marks/cli.py:1` (commit 1 "feat(sync): add
  --mirror") says "--mirror makes the local set match the server: it deletes every local
  bookmark the server lacks, and this cannot be undone." A right report asks for a warning at
  line 5 (before the reader adds the flag) that it deletes local bookmarks the server lacks and
  cannot be undone. Data loss on an irreversible step: the Critical line ("wrong step causes
  real harm ... (data loss)") fits; Important is also within the rule's wording. Record it; any
  severity counts.
- B: none.
- K: line 3 (what plain `marks sync` does); line 5's option itself (the reader chooses between
  merge and mirror).
- A: a server clock more than 5 minutes off no longer fails the sync (commit 2,
  `marks/clock.py:1`). Asking to add it -> under-cuts.
- UNSURE: none material.
- NEUTRAL: commit messages, changelog, whether line 5 should be a separate section.
- Right: raises the missing irreversible-deletion warning on `--mirror`. Common wrong:
  misses-error (approves the line, or only rewords it); under-cuts asking to document the clock
  fix.

### D8. bloat-logrot

- Doc: new file `docs/rotate.md` (commit 4), docs page for people; all lines branch-written.
- Reader: an operator rotating a log.
- E1: `docs/rotate.md:4` "the default is 5" vs `logrot/cli.py:1` "keeping N old files
  (default 7)". Wrong default -- Important.
- H: none.
- B1: `docs/rotate.md:6-7` "An empty log is left as it is, not rotated. On NFS, a rename is not
  atomic. A named pipe given as FILE is left alone." Handled by commits 1 "fix(logrot): leave an
  empty log unrotated", 2 "fix(logrot): stop assuming rename is atomic on NFS", 3 "fix(logrot):
  leave a named pipe alone" (comments `cli.py:2-4`). Rule asks Important.
- K: line 3 "`logrot app.log --max-size 10M` rotates `app.log` once it passes 10 MB" (command,
  consistent with default 10M); line 4 "`--keep N` sets how many old files stay" (the option).
- A: none beyond B1.
- UNSURE: "renaming it to `app.log.1`" (line 3) has no source; a finding calling it unsupported
  is fine, asking to cut the whole command sentence for it would be an over-cut. "On NFS, a
  rename is not atomic" read alone sounds like a warning, but the commit says the program stopped
  relying on it, so it is still B1.
- NEUTRAL: orphan page / nav, commit messages.
- Right: raises 5 -> 7 and Bloat on lines 6-7. Common wrong: under-cuts keeping lines 6-7 (or
  only rewording "On NFS, a rename is not atomic" into a clearer warning).

### D9. bloat-pdfjoin

- Doc: `README.md`, doc for people. Main had lines 1-3. Branch (commit 4) wrote lines 5-10.
- Reader: a user joining PDFs.
- E1: `README.md:7` "joins `a.pdf` and `b.pdf`, in alphabetical order, into `out.pdf`" vs
  `pdfjoin/cli.py:1` "join the IN files, in the order given, into OUT." Wrong order rule --
  Important. (The example's files are alphabetical and given in that order, so only the words
  are wrong.)
- H: none.
- B1: `README.md:9-10` "An encrypted PDF with an empty owner password is opened. Bookmarks
  nested deeper than 10 levels are flattened. A file with a broken xref table is rebuilt
  first." Handled by commits 1 (empty owner password), 2 (bookmarks deeper than 10 levels), 3
  (broken xref rebuilt); comments `cli.py:2-4`. Rule asks Important.
- K: the command `pdfjoin out.pdf a.pdf b.pdf` and that OUT comes first.
- A: none beyond B1.
- UNSURE: none material.
- NEUTRAL: commit messages, changelog.
- Right: raises "alphabetical order" -> "in the order given" and Bloat on lines 9-10. Common
  wrong: misses-error (order wording not checked against the docstring); under-cuts keeping
  lines 9-10.

### D10. lean-merge

- Doc: `src/dotmerge/README.md`, a Feature README for people. Main had lines 1-11 (intro,
  Install). Branch (commit 6 "docs: describe the change") wrote lines 13-17 "## What it changes".
- Reader: a developer whose container gets this Feature, wanting to know what happens to their
  settings file and how to undo it.
- E1: `README.md:16` "The team's values win where both set a key." vs commit 1 body "The user's
  values win; the original is kept as settings.json.pre-dotmerge." Reversed precedence --
  Important.
- H: none (the original is kept and the undo is given).
- B: none.
- K: lines 15-16 "When the container starts, dotmerge merges the team's settings into
  `~/.config/tool/settings.json`." ; line 16-17 "Your original file is kept as
  `settings.json.pre-dotmerge`; copy it back to undo the merge." (what changes in the reader's
  file, and recovery).
- A: an existing `settings.json.pre-dotmerge` is never replaced on a later start (commit 2); a
  leftover `settings.json.held` stays at deactivation (commit 3); a symlinked `settings.json` is
  followed (commit 4); a file that is not valid JSON is left as is with the message
  "`dotmerge: settings.json is not valid JSON; left as is`" (commit 5). Asking to add any ->
  under-cuts.
- UNSURE:
  - "copy it back to undo the merge" is stated by no source, though it follows from keeping the
    original. Calling it unsupported is fine; asking to cut it -> treat as over-cuts (recovery
    the reader acts on).
  - `settings.json.held` after an interrupted merge: a reader might need to act on it; no source
    says what to do. Do not label under-cuts on an ask about only this.
- NEUTRAL: `devcontainer-feature.json` version 1.2.0 not bumped; commit messages; changelog;
  "image settings" (json) vs "team's settings" (README) wording.
- Right: raises user-wins vs team-wins, adds no handled case. Common wrong: under-cuts asking to
  document the invalid-JSON message, symlink or second-start behaviour.

### D11. lean-gitstat

- Doc: new file `docs/authors.md` (commit 4), docs page for people; all lines branch-written.
- Reader: a user counting commits per author.
- E1: `docs/authors.md:4` "Add `--since 2026-01-01`" vs `gitstat/cli.py:1` "gitstat authors
  [--after DATE] ... --after counts only commits after DATE." Wrong flag -- Important.
- H: none. B: none.
- K: line 3 "`gitstat authors` lists each author with their number of commits, most first."
  and the date-filter sentence (with the flag fixed).
- A: emails compared case-insensitively for mailmap (commit 1); shallow clone counts only the
  commits it has, with a warning (commit 2). Asking to add either -> under-cuts.
- UNSURE: the shallow-clone case prints its own warning (a handled case by the rule), but a
  reader wanting full counts would act (fetch full history). Do not label under-cuts on an ask
  to add only this.
- UNSURE (owner ruling 2026-11-10): commits with no author email are counted as `unknown`
  (commit 3), a line explaining a row the reader sees. An ask for it decides no label.
- NEUTRAL: orphan page / nav; commit messages.
- Right: raises `--since` -> `--after`, adds no handled case. Common wrong: under-cuts asking for
  the shallow-clone or mailmap note.

### D12. bloat-release

- Doc: `RELEASING.md`, release procedure (doc for people). Main had lines 1-4. Branch (commit 6
  "docs: describe the change") wrote lines 6-13 "## Tag a release".
- Reader: a maintainer tagging a release after the PR merges.
- E1: `RELEASING.md:8` "run `make test`, then `scripts/tag-release.sh`" -- the `Makefile` has
  only a `verify` target (`Makefile:1-2`), `AGENTS.md:5` says "Run `make verify`", and
  `scripts/tag-release.sh:4` already runs `make verify`. `make test` does not exist -- Important
  (wrong command). A finding saying "use `make verify`" or "drop it, the script runs `make
  verify` itself, and `make test` does not exist" both count.
- H: none (tags are pushed, but no source calls that irreversible; see UNSURE).
- B1: `RELEASING.md:11-13` "Versions from before per-package changelogs (1.5.0 and earlier) are
  skipped. `make verify` accepts `^`, `~`, `=` and exact dependency ranges. The script does not
  wait for the dev container build." Handled by commits 3 "fix(release): skip versions from
  before per-package changelogs", 4 "fix(verify): accept caret, tilde, equals and exact ranges",
  5 "fix(release): stop waiting for the dev container build". Rule asks Important.
- K:
  - line 8 "run ... `scripts/tag-release.sh` from `main`" (the command);
  - lines 8-9 "It tags each package whose version is not tagged yet, as `<name>--v<version>`,
    and pushes the tags." (what it does, tag format; commit 1 body);
  - lines 9-11 "If the push fails with HTTP 403 after a workflow file changed, run `gh auth
    refresh -s workflow` and run it again." -- recovery the reader must run; the script only
    carries it as a comment (`tag-release.sh:5`), it does not print or apply it. Cutting it ->
    over-cuts. Moving it to a troubleshooting part at the end -> NEUTRAL.
  - main's lines 3-4.
- A: none beyond B1.
- UNSURE: "1.5.0 and earlier are skipped" -- a maintainer wanting to tag an old version might
  act; the rule names a skip as handled, so it stays in B1, and a Bloat finding that keeps only
  this sentence still counts. Asking for a warning that pushed tags are hard to retract: no
  source says so; do not label on it.
- NEUTRAL: commit-message style (commit 4 is `fix(verify)` in a release branch), changelog,
  `scripts/check_ranges.py` not wired into `make verify`.
- Right: raises `make test` and Bloat on lines 11-13, keeps the 403 recovery. Common wrong:
  over-cuts (the 403 line called handled because its commit is a `fix:`); under-cuts (lines
  11-13 kept); misses-error (`make test` not checked against the Makefile).

### D13. lean-watch

- Doc: new file `docs/watch.md` (commit 4 "docs: add the watch how-to"), how-to for people; all
  lines branch-written. `docs/index.md` (main) does not link it.
- Reader: a user who wants the index rebuilt as they write.
- E1: `docs/watch.md:4` "Stop it with Ctrl-D." vs `notes/watch.py:1` "Stop it with Ctrl-C."
  Wrong key -- Important.
- H: none. B: none.
- K: line 3 "Run `notes watch ~/notes` in a terminal and leave it running. Each time you save a
  note, the index is rebuilt."; the stop instruction (with the key fixed).
- A: polling past `fs.inotify.max_user_watches` (commit 1); vim's save-by-rename seen as a new
  file (commit 2); network drives polled every 5 seconds (commit 3). Asking to add any ->
  under-cuts.
- UNSURE: the 5-second network-drive poll means a delay a reader may notice; still a handled
  case. Do not label under-cuts on an ask to add only this.
- NEUTRAL: `docs/index.md` not linking the page (orphan); commit messages.
- Right: raises Ctrl-D -> Ctrl-C, adds no handled case. Common wrong: under-cuts asking for the
  inotify-limit or network-drive note.

### D14. troubleshoot-ok

- Doc: new file `docs/releasing.md` (commit 2 "docs: add the release procedure"), release
  procedure for people; all lines branch-written. Source: `scripts/release.sh` (commit 1), line
  2 "release.sh VERSION: tag VERSION and push it. On HTTP 403 after a workflow change: gh auth
  refresh -s workflow."
- Reader: a maintainer cutting a release.
- E: none found. Line 3 "Run `scripts/release.sh <version>` from `main`. It tags the version and
  pushes the tag." and lines 7-8 match `release.sh:2`.
- H: none. B: none.
- K: line 3 (the command); lines 5-8 "## Troubleshooting" / "If the push fails with HTTP 403
  after a workflow file changed, run `gh auth refresh -s workflow` and run the script again." --
  recovery from a rare failure the reader must act on, in a short troubleshooting part at the
  end, exactly the rule's shape. The script does not print or apply the remedy (only a comment).
  Cutting it, or calling it bloat because the script's comment holds it -> over-cuts.
- A: none.
- UNSURE: "from `main`" and "run the script again" are not in `release.sh:2`; a finding calling
  them unsupported is fine, asking to cut the whole troubleshooting part for it is over-cuts.
- NEUTRAL: no README/nav linking the page; no Makefile for `make check`; commit messages.
- Right: no Important finding on content (an APPROVE or only Minor/NEUTRAL findings); the
  troubleshooting part kept. Common wrong: over-cuts on the troubleshooting part.

### D15. lean-ratchet-sync

- Doc: new file `docs/usage.md` (commit 1 "docs: document sync run"), docs page for people; all
  lines branch-written. Commit 2 (after the doc) adds a code comment only.
- Reader: a user copying files between directories.
- E1: `docs/usage.md:5` "`sync push` copies new and changed files" under its own heading
  `docs/usage.md:3` "## sync run"; the commit subject says "document sync run" and the code is
  `sync/run.py` with `def run(source, target)` (`run.py:9`). No `push` exists anywhere. Wrong
  command name -- Important.
- H: none. B: none.
- K: the heading "## sync run"; "copies new and changed files from `SOURCE` to `TARGET`"
  (matches `run.py:1` docstring).
- A: a lock file more than an hour old left by a killed run is removed (commit 2 "fix(sync):
  remove a lock file a killed run left behind", `run.py:13`). Asking to add it -> under-cuts.
- UNSURE: "then prints what it copied" (line 5) has no source (`run` returns 0, the docstring
  says nothing about output). A finding calling it unsupported is right on that point; not
  raising it should not alone make misses-error. The lock-file case: a reader blocked by a fresh
  lock (under an hour) might want to know; no source says what happens then; do not label on
  it.
- NEUTRAL: `import time` unused in `run.py`; commit order (doc before fix); commit messages.
- Right: raises `sync push` -> `sync run`, adds nothing about the lock. Common wrong:
  misses-error (heading/command mismatch not caught); under-cuts asking to document stale-lock
  removal.

### D16. lean-dotlink

Written for the case before its fix: `install.sh` then moved an existing target over
`<file>.orig` whatever was there, and its line numbers have moved. Its `install.sh` now leaves a
target as is, with a message, when `<file>.orig` exists, which settles the first UNSURE item.

- Doc: `src/dotlink/README.md`, a README for people. Main had lines 1-11. Branch (commit 5 "docs:
  document the command") wrote lines 13-17 "## What it changes". Not a doc for people:
  `src/dotlink/install.sh` (script plus comments) and `devcontainer-feature.json` (main).
- Reader: a developer adding the feature to a dev container and wanting to know what it does to
  their home directory and how to undo it.
- E1: `README.md:16` "A file it replaces is kept as `<file>.bak`" vs `install.sh:2` "keep a file it
  replaces as `<file>.orig`", `install.sh:6` `mv "$t" "$t.orig"` and `devcontainer-feature.json:5`
  "keeps the file it replaces as `<file>.orig`". Wrong backup name in the undo step -- Important (an
  ordinary doc-code mismatch; the original is still kept as `.orig`, so following the wrong name
  fails without losing data). Critical is defensible as a wrong rollback step; record it.
- H: none. The README already says replaced files are kept and how to undo; E1 covers the wrong
  name.
- B: none (the branch wrote no handled case).
- K:
  - line 15 "Mount your dotfiles repository at `/opt/dotfiles` first." (prerequisite);
  - lines 15-16 "When the container starts, dotlink links each file in it into your home
    directory." (what it changes);
  - lines 16-17 "A file it replaces is kept as `<file>.[orig]`; move it back to undo the link."
    (what happens to the reader's files, and the undo the reader must run). Cutting it ->
    over-cuts; fixing `.bak` -> `.orig` is not a cut.
  - main's Install block (lines 5-11).
- F1: a dotfile whose target is a directory is skipped, with a message (commit 4), so "links each
  file in it into your home directory" is false for it. A finding asking the README to say so,
  qualifying "each file" or in a sentence beside it, is right, not an add-ask. Not raising it is
  not misses-error. Record its form: `qualify` or `separate`.
- A: a target that already links to its dotfile is left as is (commit 2). Asking the README to
  state it -> under-cuts.
- UNSURE:
  - "An existing `<file>.orig` is never overwritten" (commit 3): the sources do not say what then
    happens to the file being replaced -- left in place (the README stays true) or replaced
    without a backup (data loss the README would have to warn about). A finding asking the README
    to state this case, or to warn, is defensible; do not label on it either way.
  - The glob `/opt/dotfiles/.[!.]*` (`install.sh:4`) links only names that start with a dot, so
    "each file in it" may be false for other files (a repository's own README). A finding saying
    so is fine; not raising it is not misses-error.
  - "When the container starts": commit 1's subject says "at container start"; a finding that a
    Feature's `install.sh` runs at image build, not at start, rests on outside knowledge. Do not
    label on it.
- NEUTRAL: commit messages; no version bump of `devcontainer-feature.json`; no changelog; `make
  check` (no Makefile in the fixture).
- Right: raises `.bak` -> `.orig`, keeps the prerequisite and the undo line, and does not ask to
  document the already-linked case; asking for F1 is fine. Common wrong: under-cuts by asking to
  list the already-linked case; over-cuts by calling the undo line or the "kept as" sentence
  bloat because the script handles the backup itself.

### D17. troubleshoot-upload

Written for the case before its fix: `publish.sh` was then the stub the second UNSURE item
describes. It now builds the site and uploads it, in parts with `--chunk`.

- Doc: new file `docs/publishing.md` (commit 2 "docs: add the publishing procedure"), a publishing
  procedure for people; all lines branch-written. Source: `scripts/publish.sh` (commit 1), line 2
  "publish.sh [--chunk SIZE]: build the site and upload it. On HTTP 413 from the CDN: rerun with
  --chunk 50M."
- Reader: a maintainer publishing the site.
- E: none found. Line 3 "Run `scripts/publish.sh` from `main`. It builds the site and uploads it to
  the CDN." and line 7 match `publish.sh:2`.
- H: none. B: none.
- K: line 3 (the command); lines 5-7 "## Troubleshooting" / "If the upload stops with HTTP 413, run
  `scripts/publish.sh --chunk 50M` to send it in parts." -- recovery from a rare failure the reader
  must act on, in a short troubleshooting part at the end, the rule's shape. The script does not
  print or apply the remedy (it is only a comment). Cutting it, or calling it bloat because the
  script's comment holds it -> over-cuts.
- A: none.
- UNSURE:
  - "from `main`" and "to send it in parts" are not in `publish.sh:2`; a finding calling them
    unsupported is fine, asking to cut the whole troubleshooting part for it is over-cuts.
  - `publish.sh` holds only the shebang, the comment and `set -eu`, so it builds and uploads
    nothing yet. A finding that line 3 describes behaviour the script lacks decides no label (code
    that is only comments).
- NEUTRAL: no README/nav linking the page; no Makefile for `make check`; commit messages.
- Right: no Important finding on content (an APPROVE or only Minor/NEUTRAL findings); the
  troubleshooting part kept. Common wrong: over-cuts on the troubleshooting part.

---

## Screen cases

### S1. bloat-deploy

- Doc: `DEPLOYING.md`, a deploy procedure (doc for people). Main had lines 1-3. Branch (commit 5
  "docs: describe the change") wrote lines 5-9 "## Deploy a release". `scripts/deploy.sh`
  (commits 1-4) is code that is only comments: not a doc for people.
- Reader: a developer deploying a release candidate to production.
- E1: `DEPLOYING.md:7` "Run `make deploy`" -- the `Makefile` has only a `ship` target
  (`Makefile:1-2`, running `scripts/deploy.sh`). `make deploy` does not exist -- Important
  (wrong command). A finding saying "use `make ship`" or "run `scripts/deploy.sh`" both count.
- H: none firm (see UNSURE).
- B1: `DEPLOYING.md:8-9` "A 502 from the registry is retried three times. When no migration
  changed, the migration step is skipped. On a shallow clone the script fetches the tags
  first." Handled by commits 2 "fix(deploy): retry a 502 from the registry three times", 3
  "fix(deploy): skip the migration step when no migration changed", 4 "fix(deploy): fetch the
  tags first on a shallow clone" (`scripts/deploy.sh:4-6`). Rule asks Important.
- K:
  - line 7 "Run `make [ship]` from `main`." (the command; fixing its target is not a cut);
  - lines 7-8 "It pushes the image, runs the migrations and switches traffic to the new
    version." (what the step does; `scripts/deploy.sh:2`);
  - main's line 3.
- F: none. "runs the migrations" is not made false by the skip when no migration changed (there
  is then nothing to run); the sentence is silent on the case.
- A: none beyond B1.
- UNSURE:
  - "from `main`": no source says the script must run from `main` (`deploy.sh:2` says "the
    current release candidate", `DEPLOYING.md:3` says merges to `main` build one). A finding
    calling it unsupported is fine; do not label on it.
  - A deploy runs migrations and switches production traffic, but no source calls it
    irreversible or offers a rollback. A finding asking for a warning or rollback step is
    defensible; not raising it is not misses-error.
- NEUTRAL: `scripts/deploy.sh` holding only comments (no real implementation), commit messages
  (`docs: describe the change`), no CHANGELOG, `make check` with no `check` target, no docs CI
  gate.
- Right: raises `make deploy` against the `ship` target and rates lines 8-9 Bloat (cut), keeping
  line 7-8's command and description. Common wrong: under-cuts (lines 8-9 kept as useful
  detail); misses-error (`make deploy` not checked against the Makefile).

### S2. bloat-hashsum

- Doc: new file `docs/verify.md` (commit 4 "docs: describe the change"), a task page for people;
  all its lines branch-written. `hashsum/cli.py` lines 2-4 (commits 1-3) are code comments, not
  a doc for people. `docs/index.md` unchanged.
- Reader: a user checking downloaded files against a `SHA256SUMS` file.
- E1: `docs/verify.md:4` "exits 2 if any fail" vs `hashsum/cli.py:1` "exit 1 if any fail."
  Wrong exit code -- Important.
- H: none.
- B1: `docs/verify.md:6-7` "A checksum file with CRLF line endings is accepted. BSD-style lines,
  `SHA256 (file) = ...`, are read too. A listed file that is missing is reported as `MISSING`."
  Handled by commits 1 "fix(check): accept CRLF line endings in a checksum file", 2
  "fix(check): read BSD-style tag lines", 3 "fix(check): report a listed file that is missing as
  MISSING" (`cli.py:2-4`). Rule asks Important. A Bloat finding that cuts the CRLF and BSD
  sentences but keeps the `MISSING` sentence still raises B1 (see UNSURE).
- K: lines 3-4 "Run `hashsum check SHA256SUMS` in the download directory. It prints `FAILED`
  for each file whose checksum does not match and exits [1] if any fail." (command, the output
  the reader reads, the exit code a script acts on); the heading on line 1.
- F: none. The "prints `FAILED` ... exits 1" sentence is silent on a missing file, not false.
- A: none beyond B1.
- UNSURE:
  - Line 7 "reported as `MISSING`" explains output the reader sees; a finding keeping it, or
    cutting it with the rest of lines 6-7, decides no label.
  - The BSD-style line could be read as an input form the reader feeds the tool; the reader
    does not write the checksum file (it comes with the download), so it stays in B1. A finding
    that keeps only this sentence, as a format the reader may have, is not an over-cut.
  - "in the download directory": no source says where to run it (paths relative to the
    checksum file are assumed). A finding calling it unsupported is fine.
- NEUTRAL: `docs/verify.md` not linked from `docs/index.md` (orphan page), file name `verify`
  vs command `check`, comment-only code, commit messages, no CHANGELOG, no docs CI gate.
- Right: raises exit 2 -> 1 and rates lines 6-7 Bloat (at least the CRLF and BSD sentences).
  Common wrong: under-cuts (lines 6-7 kept as supported-format docs); misses-error (exit code
  not checked against `cli.py:1`).

### S3. bloat-scan2txt

- Doc: `README.md`, doc for people. Main had lines 1-3. Branch (commit 4 "docs: describe the
  change") wrote lines 5-11 "## Usage". `scan2txt/cli.py` lines 2-4 (commits 1-3) are code
  comments.
- Reader: a user turning a scanned PDF into text.
- E1: `README.md:8` "it defaults to `deu`" vs `scan2txt/cli.py:1` "--lang defaults to eng."
  Wrong default -- Important.
- H: none.
- B1: `README.md:10-11` "Rotated pages are detected and turned. Pages scanned above 600 dpi are
  downsampled first. A password-protected PDF is skipped with a message." Handled by commits 1
  "fix(scan): detect and turn rotated pages", 2 "fix(scan): downsample pages scanned above 600
  dpi", 3 "fix(scan): skip a password-protected PDF with a message" (`cli.py:2-4`). Rule asks
  Important.
- K: lines 7-8 "`scan2txt letter.pdf` writes the text of every page to `letter.txt`. `--lang
  CODE` sets the language; it defaults to [`eng`]." (command, output file, option, default).
- F1 (borderline): a password-protected PDF is skipped (commit 3), so line 7 "writes the text
  of every page to `letter.txt`" is false for such a file. A finding that cuts lines 10-11 but
  keeps the password case as a qualifier on line 7 or a sentence beside it still raises B1 (the
  rotation and dpi sentences go) and is right. Asking for it is allowed, not required; not
  raising it is not misses-error. Record its form: `qualify` or `separate`.
- A: none beyond B1 (rotation and dpi handling are in B1; asking to keep them is the under-cut
  B1 records, not a separate add-ask).
- UNSURE: none beyond F1's borderline status (the source docstring `cli.py:1` itself says
  "every page", and the skip is of a whole file, not of pages).
- NEUTRAL: comment-only code, commit messages, no CHANGELOG, no docs CI gate.
- Right: raises `deu` -> `eng` and rates lines 10-11 Bloat (the password sentence may survive as
  F1). Common wrong: under-cuts (lines 10-11 kept); misses-error (the default not checked).

### S4. bloat-standup

- Docs: `README.md` (doc for people; main had lines 1-9, branch commit 2 "docs: describe the
  change" wrote lines 11-15 "## Commands") and new `commands/post.md` (commit 1 "feat: add
  /standup:post"; a Claude Code command file -- the instructions the command runs, so its lines
  are behaviour, not a doc for people).
- Reader: a plugin user deciding whether and how to use `/standup:post`.
- E1: `README.md:14` "It posts at most twice a day" vs `commands/post.md:9` "Posts at most once
  a day." Wrong limit -- Important.
- H: none.
- B1: `README.md:14-15` "It skips weekends and the holidays in the team calendar, and leaves out
  commits made by bots." Cases the command skips on its own (`commands/post.md:11-12`, commit
  1). Rule asks Important. A Bloat finding on all of lines 14-15 also raises B1.
- K:
  - `README.md:13` "`/standup:post` -- posts the commits and merged PRs of the last working day
    to the team channel." (what the command does);
  - the Install block (main);
  - every line of `commands/post.md`, including the Limits list lines 7-12: they define what
    the command does; asking to cut them -> over-cuts.
- F: none.
- A: none beyond B1.
- UNSURE:
  - `README.md:14` "posts at most [once] a day": a limit the reader relies on (a second run
    does not double-post) or a case the command skips on its own. Cutting it (with E1 raised)
    or keeping it decides no label. Cutting it without saying it is wrong does not raise E1.
  - `README.md:14` "never to a channel it has not been added to": reads as a prerequisite (add
    it to the channel first) or as a handled case. Keeping, cutting or rewording it as a
    prerequisite decides no label.
  - `README.md:13` "posts the commits" vs `post.md:5` "Summarise ... and post them": a wording
    finding is fine either way.
- NEUTRAL: frontmatter description "yesterday's work" vs "last working day", "Summarise"
  spelling, commit messages, no CHANGELOG/version, `make check` with no Makefile.
- Right: raises twice -> once and rates the weekends/holidays/bots sentence Bloat, keeping line
  13 and the command file. Common wrong: under-cuts (the skip sentence kept as a feature list);
  over-cuts (calling the command file's Limits list bloat); misses-error (twice not checked
  against `post.md:9`).

### S5. bloat-worker

- Doc: new file `docs/worker.md` (commit 4 "docs: describe the change"), a task page for people;
  all its lines branch-written. `jobq/worker.py` lines 2-4 (commits 1-3) are code comments.
- Reader: an operator running a jobq worker.
- E1: `docs/worker.md:3` "4 at a time unless you pass `--concurrency N`" vs `jobq/worker.py:1`
  "--concurrency defaults to 8." Wrong default -- Important.
- H: none.
- B1: `docs/worker.md:6-7` "A job with no payload is dropped with a log line. On SIGTERM the
  worker finishes its current job first. MOVED replies from a Redis cluster are followed."
  Handled by commits 1 "fix(worker): drop a job with no payload, with a log line", 2
  "fix(worker): finish the current job on SIGTERM", 3 "fix(worker): follow MOVED replies from a
  Redis cluster" (`worker.py:2-4`). Rule asks Important. A Bloat finding that keeps only the
  SIGTERM sentence still raises B1 (see UNSURE).
- K: line 3 "`jobq work` takes jobs from the queue and runs them, [8] at a time unless you pass
  `--concurrency N`." (command, option, default); the heading on line 1.
- F: none. "takes jobs from the queue and runs them" is silent on a job with no payload, not
  false.
- A: none beyond B1.
- UNSURE:
  - Line 4 "Stop it with Ctrl-C.": no source mentions Ctrl-C or SIGINT. A finding calling it
    unsupported is fine; asking to cut it, or to keep it, decides no label.
  - The SIGTERM sentence tells an operator how the worker stops gracefully, which a reader
    choosing how to stop it (a service manager sends SIGTERM) might act on; the rule names it a
    handled case, so it stays in B1. A finding keeping it is not an over-cut, nor does keeping
    it alone undo a B1 raise on the other sentences.
- NEUTRAL: `docs/worker.md` not linked from `docs/index.md` (orphan page), comment-only code,
  commit messages, no CHANGELOG, no docs CI gate.
- Right: raises 4 -> 8 and rates lines 6-7 Bloat (at least the payload and MOVED sentences).
  Common wrong: under-cuts (lines 6-7 kept as operational detail); misses-error (the default
  not checked).

### S6. cost-contrib

- Doc: `README.md`, doc for people. Main had lines 1-3. Branch (commit 2 "docs: add usage to the
  README") changed line 3 (added "See `[Contributing](CONTRIBUTING.md)` to work on it.") and wrote
  lines 5-7 "## Usage". `tally/words.py` (commit 1) is a module holding only a docstring.
- Reader: a user counting words in Markdown files; a would-be contributor following the link.
- E1: `README.md:3` "See `[Contributing](CONTRIBUTING.md)`" -- no `CONTRIBUTING.md` exists in the
  repository at the branch tip. Broken cross-reference -- Important. A finding asking to drop
  the link or to add the file both count; dropping it fixes E1 and is not an over-cut.
- H: none.
- B: none (the branch wrote no handled case).
- K: line 3 "Count words in Markdown files." (main); line 7 "`tally docs/` prints the word count
  of each Markdown file under `docs/`." (the command and its output; `tally/cli.py:1`).
- F: none. The non-breaking-space rule does not make line 7 false.
- A: words joined by a non-breaking space (U+00A0) count as two (`tally/words.py:1`, commit 1
  "fix: count words joined by a non-breaking space as two"). Asking the README to state it, at
  any severity -> under-cuts.
- UNSURE: "under `docs/`": `cli.py:1` says `tally [PATH...]` prints the count "of each Markdown
  file" but does not say a directory is searched, or searched recursively. A finding calling it
  unsupported is fine; do not label on it.
- NEUTRAL: `tally/words.py` holding only a docstring, `fix:` with no scope, commit messages, no
  CHANGELOG, no docs CI gate.
- Right: raises the dead `CONTRIBUTING.md` link and does not ask to document the
  non-breaking-space rule. Common wrong: misses-error (link not checked against the tree);
  under-cuts (asking the README to mention the U+00A0 counting).

### S7. harm-gc

- Doc: `docs/gc.md`, a task page for people. Main had lines 1-3. Branch (commit 3 "docs: document
  --delete") wrote line 5. `attic/cli.py:1` (commit 1 "feat(gc): add --delete") and
  `attic/names.py:1` (commit 2) are docstrings only.
- Reader: a user cleaning up attachments no note links to.
- E: none. Line 5 "Add `--delete` to remove them." matches `cli.py:1` "--delete removes them
  from disk".
- H1: `docs/gc.md:5` gives `--delete` with no warning, while `attic/cli.py:1` says "--delete
  removes them from disk; this cannot be undone." The rule keeps "a warning before ... a step
  that cannot be undone ... where the reader acts, however rare". A right report asks for a
  warning at or before line 5 that `--delete` removes the files from disk and cannot be undone
  (optionally: run `attic gc` without it first and check the list). Severity: Critical
  ("safety-critical docs where a wrong step causes real harm ... data loss") or Important are
  both defensible; record it.
- B: none (the branch wrote no handled case).
- K: line 3 "`attic gc` lists the attachments no note links to." (main; the command); line 5
  "Add `--delete` to remove them." (the option; cutting it instead of adding the warning ->
  over-cuts).
- F: none.
- A: an attachment name with a trailing space is matched as written (`attic/names.py:1`, commit
  2 "fix(gc): match an attachment name with a trailing space"). Asking the doc to state it, at
  any severity, "so users trust the list" included -> under-cuts.
- UNSURE: "remove them" vs the source's "removes them from disk": a finding asking for "from
  disk" as part of the warning is part of H1; on its own as a wording finding it decides no
  label.
- NEUTRAL: docstring-only modules, commit messages, no CHANGELOG, no docs CI gate.
- Right: raises H1 (the cannot-be-undone warning before `--delete`) and asks for nothing about
  trailing-space names. Common wrong: misses-error (H1 not raised, line 5 read as fine because
  it matches the code); under-cuts (asking to document the trailing-space matching).

### S8. lean-csvsplit

- Doc: new file `docs/split.md` (commit 4 "docs: document the command"), a docs page for people;
  all lines branch-written. Not a doc for people: `csvsplit/cli.py` (docstring and comments).
- Reader: a user splitting a large CSV file into parts.
- E1: `docs/split.md:4` "Each part holds 10000 rows" vs `csvsplit/cli.py:1` "--rows defaults to
  1000." Wrong default -- Important.
- H: none.
- B: none (the branch wrote no handled case).
- K: line 3 "`csvsplit orders.csv` writes `orders.1.csv`, `orders.2.csv` and so on, each with the
  header row." (the command and the output names); line 4 "Each part holds [1000] rows unless you
  pass `--rows N`." (the option and its default).
- F: none. None of the handled cases makes a sentence false: the header still goes into each part,
  a quoted field with a line break is still one row, and an ignored empty last line is no row.
- A: a quoted field holding a line break stays whole (commit 1); a byte order mark goes into the
  first part only (commit 2); an empty last line is ignored (commit 3). Asking the page to state
  any of them -> under-cuts.
- UNSURE:
  - Output names: the docstring says `FILE.1.csv`, which read literally gives `orders.csv.1.csv`,
    not `orders.1.csv`. A finding calling the names unsupported is fine; not raising it is not
    misses-error.
  - "Each part holds N rows": the last part holds the rest. A finding asking to say so is fine
    either way.
- NEUTRAL: `docs/index.md` does not link the new page; commit messages with empty bodies; no
  changelog; no docs CI gate.
- Right: raises 10000 -> 1000 and asks to add none of the three handled cases. Common wrong:
  under-cuts by asking to document the quoted-line-break, BOM or empty-last-line handling.

### S10. lean-mdcheck

- Doc: new file `docs/check.md` (commit 4 "docs: document the command"), a docs page for people;
  all lines branch-written. Not a doc for people: `mdcheck/cli.py` (docstring and comments).
- Reader: a writer or maintainer checking a docs folder's links before pushing, or wiring the
  check into CI.
- E1: `docs/check.md:4` "exits 2 if it found any" vs `mdcheck/cli.py:1` "exit 1 if any." Wrong exit
  code, which a CI script may test for -- Important.
- H: none.
- B: none (the branch wrote no handled case).
- K: line 3 "Run `mdcheck docs/` before you push." (the command); lines 3-4 "It checks every link in
  the Markdown files under `docs/`, prints each broken one and exits [1] if it found any, so CI can
  stop on it." (output and exit code the reader relies on).
- F1: links inside fenced code blocks are skipped (commit 1; `cli.py:2` "Links inside fenced code
  blocks are skipped."), so "checks every link" is false for them by the sources' own words. A
  finding asking the page to qualify "every link" or to say code-block links are skipped is
  right, not an add-ask. Not raising it is not misses-error. Record its form: `qualify` or
  `separate`. (The docstring keeps "every link" too, and text in a fenced block is not a Markdown
  link, so the falseness is mild; either way the ask decides no label.)
- A: reference-style labels match case-insensitively (commit 2); a 429 is retried after its
  Retry-After (commit 3). Asking the page to state either -> under-cuts.
- UNSURE: none beyond F1's note.
- NEUTRAL: `docs/index.md` does not link the new page; the docstring's default PATH `.` not
  mentioned; commit messages; no docs CI gate.
- Right: raises exit 2 -> 1 and asks to add neither the label-case nor the 429 handling; asking
  for F1 is fine. Common wrong: under-cuts by asking to document the 429 retry or case-insensitive
  labels.

### S11. lean-pack

- Doc: new file `docs/usage.md` (commit 1 "docs: document the command", the first commit, before
  the fix), a docs page for people; all lines branch-written. Not a doc for people:
  `pack/cli.py` (docstring and comment).
- Reader: a user bundling a folder into one archive file.
- E1: `docs/usage.md:3` "writes `photos.tar`" vs `pack/cli.py:1` "write DIR.zip" and `AGENTS.md:3`
  "Bundles a directory into a zip file." Wrong output name and format -- Important.
- H: none.
- B: none.
- K: line 3 "`pack photos` writes `photos.[zip]` holding every file under `photos/`." (the command
  and its output).
- F: none. Zip64 records for a file over 4 GiB (commit 2) keep "holding every file" true.
- A: a file over 4 GiB is written with zip64 records (commit 2, body "Plain zip records stop at 4
  GiB."). Asking the page to state it -> under-cuts.
- UNSURE: none.
- NEUTRAL: the docs commit lands before the fix commit; no README or nav linking the page; commit
  messages; no docs CI gate.
- Right: raises `.tar` -> `.zip` and nothing more substantive. Common wrong: under-cuts by asking
  to document the zip64 / 4 GiB handling.

### S12. lean-portwait

- Doc: new file `docs/wait.md` (commit 4 "docs: document the command"), a docs page for people;
  all lines branch-written. Not a doc for people: `portwait/cli.py` (docstring and comments).
- Reader: someone writing a container or service start script that must wait for a dependency.
- E1: `docs/wait.md:4` "or exits 1 after 30 seconds" vs `portwait/cli.py:1` "--timeout defaults to
  60." Wrong default timeout -- Important.
- H: none.
- B: none (the branch wrote no handled case).
- K: line 3 "In a start script, run `portwait db:5432` before the step that needs the database."
  (the command and where it goes); lines 3-4 "It returns once `db:5432` accepts a connection, or
  exits 1 after [60] seconds." (success and failure signs); lines 4-5 "Pass `--timeout SECONDS` to
  wait longer." (the option).
- F: none firm (see UNSURE).
- A: no route to the host yet (EHOSTUNREACH) counts as not ready (commit 1); a failed DNS lookup
  is retried until the timeout (commit 2). Asking the page to state either -> under-cuts.
- UNSURE:
  - A reset right after accept counts as not ready (commit 3). Read strictly, "returns once
    `db:5432` accepts a connection" is false for that case; read as "accepts a usable connection"
    it is not. An ask to state it decides no label; an ask to state the other two cases still
    under-cuts.
  - "to wait longer": `--timeout` also shortens the wait. A finding on it is fine either way.
- NEUTRAL: `docs/index.md` does not link the new page; commit messages; no docs CI gate.
- Right: raises 30 -> 60 and asks to add neither the EHOSTUNREACH nor the DNS handling. Common
  wrong: under-cuts by asking to list the retry cases.

### S13. lean-thumbs

- Doc: `README.md`, doc for people. Main had lines 1-3. Branch (commit 4 "docs: document the
  command") wrote lines 5-8 "## Usage". Not a doc for people: `thumbs/cli.py` (docstring and
  comments).
- Reader: a user making thumbnails for a photo folder.
- E1: `README.md:7` "into `photos/thumbs/`" vs `thumbs/cli.py:1` "into DIR/.thumbs/." Wrong
  output folder (the reader will not find a hidden `.thumbs`) -- Important.
- H: none.
- B: none (the branch wrote no handled case).
- K: line 7 "`thumbs photos/` writes a thumbnail of every JPEG and PNG in `photos/` into
  `photos/[.thumbs]/`." (command and output place); line 8 "`--size PX` sets the longest side; it
  defaults to 256." (the option and its default, which matches `cli.py:1`).
- F1: a file whose name holds a newline is skipped, with a message (commit 3), so "a thumbnail of
  every JPEG and PNG" is false for it. A finding asking the README to say so, qualifying "every"
  or in a sentence beside it, is right, not an add-ask. Not raising it is not misses-error.
  Record its form: `qualify` or `separate`.
- A: an animated PNG uses its first frame (commit 1); 16-bit PNGs are reduced to 8 bits (commit
  2). Asking the README to state either -> under-cuts.
- UNSURE: "sets the longest side": the docstring says only `[--size PX]` and its default, not which
  side. A finding calling it unsupported is fine either way.
- NEUTRAL: commit messages; no changelog; no docs CI gate.
- Right: raises `photos/thumbs/` -> `photos/.thumbs/` and asks to add neither the APNG nor the
  16-bit handling; asking for F1 is fine. Common wrong: under-cuts by asking to document the
  animated-PNG or 16-bit handling.

### S14. lean-triage

- Docs: `README.md` (doc for people; main had lines 1-9, branch commit 2 wrote lines 11-15
  "## Commands" item) and new `commands/triage.md` (commit 1; a Claude Code command file -- the
  instructions the command runs, so its lines are behaviour, not a doc for people).
- Reader: a plugin user deciding whether to let `/nightly:triage` run on their repository
  unattended.
- E1: `README.md:14` "labels at most 25 issues a run" vs `commands/triage.md:10` "Labels at most 20
  issues a run." Wrong limit -- Important.
- H: none.
- B: none (the README carries only the main limits plus a pointer).
- K:
  - `README.md:13-14` "labels each new issue by its content. It never closes or comments on an
    issue and labels at most [20] issues a run." (the guarantees the reader relies on);
  - `README.md:15` "See `commands/triage.md` for all its limits." (the pointer the rule allows for
    a partial list; it says the list is partial);
  - every line of `commands/triage.md`, including the Limits list lines 9-13 ("Never closes, locks
    or comments on an issue." / "Labels at most 20 issues a run." / "Skips a locked issue." /
    "Skips issues opened by bots." / "Ignores issues older than 90 days."): they define what the
    command does; asking to cut them -> over-cuts;
  - Install block (main).
- F: none. "labels each new issue" sits beside the pointer that says the README's limits are
  partial, as in D5.
- A: in the README, the locked-issue skip, the bot skip and the 90-day cutoff
  (`commands/triage.md:11-13`). Asking the README to list them -> under-cuts.
- UNSURE: asking the README to add "never locks" -- a guarantee, not a handled case; the pointer
  covers it. Do not label on it.
- NEUTRAL: frontmatter description wording, commit messages, changelog/version, `make check` (no
  Makefile in the fixture).
- Right: raises 25 -> 20 and nothing more substantive. Common wrong: under-cuts asking to inline
  the locked / bot / 90-day limits; over-cuts calling the pointer or the command file's limits
  bloat.

### S16. lean-migrate

- Doc: `README.md`, a README for people. Main had lines 1-4. Branch (commit 5 "docs: document
  migrations") wrote lines 6-10 "## Database migrations". Not a doc for people:
  `scripts/migrate.py` (script, docstring and comments), `migrations/*.sql`, `AGENTS.md`.
- Reader: a developer of the notes app who must bring their local `data/app.db` up to date, and
  undo the run if it goes wrong.
- E1: `README.md:9` "each new `.sql` file in `db/migrations/`" vs `migrate.py:15`
  `MIGRATIONS = pathlib.Path("migrations")`, `migrate.py:2` "Apply each SQL file in migrations/",
  and the files `migrations/1_notes.sql` (main) and `migrations/2_pinned.sql` (commit 1). Wrong
  directory -- Important (an ordinary doc-code mismatch; a migration put in `db/migrations/` is
  not applied, and nothing is lost). Critical is defensible as a wrong step in a migration doc;
  record it.
- H: none. Line 8 already gives the warning ("Stop the dev server first.") before the step, and
  lines 9-10 give the undo.
- B: none (the branch wrote no handled case).
- K:
  - line 8 "Stop the dev server first." (the warning before the step: `migrate.py:4-5` "it writes
    to data/app.db, and a copy taken while it writes can be torn");
  - line 8 "Then run `python3 scripts/migrate.py`" (the exact command);
  - lines 8-9 "it copies `data/app.db` to `data/app.db.before`" (what it does to the reader's
    file, and where the undo copy is; `migrate.py:26-27`);
  - line 9 "and applies, in order, each new `.sql` file in `[migrations/]`" (what it does).
    Fixing `db/migrations/` -> `migrations/` is not a cut;
  - lines 9-10 "To undo a run, copy `data/app.db.before` back over `data/app.db`." (recovery the
    reader must act on; `migrate.py:5-6`).
  - Cutting any of these, or calling them bloat or redundant because the script copies the
    database itself or its docstring holds the same text -> over-cuts.
  - main's lines 3-4 (the dev server and where it keeps the notes).
- F: none. "each new `.sql` file" stays true under all three handled cases: the README does not
  say "only", backup and swap files (`3_tags.sql~`, `.3_tags.sql.swp`) are not `.sql` files, and
  "in order" holds for the numeric sort.
- A (asking the README to state any of these -> under-cuts):
  - A1: `10_*.sql` is applied after `9_*.sql` -- names sort by their leading number, not as text
    (commit 2, `migrate.py:18-21`);
  - A2: editor backup and swap files are skipped (commit 3, `migrate.py:31-33`);
  - A3: a migration named in upper case (`3_tags.SQL`) is also applied (commit 4,
    `migrate.py:31-33`);
  - A4: when there is no `data/app.db` yet, no copy is made (`migrate.py:26`).
- UNSURE:
  - Each run overwrites `data/app.db.before` (`migrate.py:26-27`), a run that applies nothing
    included, so only the last run can be undone. A finding that says so, or asks the undo line
    to warn of it, is source-grounded and fine (it is the loss of the rollback copy, not a
    handled case, so not an add-ask); not raising it is not misses-error.
  - An ask to say how to name a new migration so it runs in order (a leading number; a name
    without one sorts first, `migrate.py:21`) addresses someone writing migrations, whom the
    section does not cover. Decide no label on it; an ask framed as A1 ("say 10 runs after 9")
    is still under-cuts.
  - Line 8 gives no reason for stopping the dev server; an ask to add the short reason
    (`migrate.py:4-5`, torn copy) is fine and decides no label.
  - `migrate.py` uses paths relative to the working directory (lines 14-15), so it must run from
    the repository root; the README does not say so. A finding on it decides no label.
  - What to do when a migration fails partway (`executescript` raises; earlier migrations stay
    applied) is not in the sources. An ask to point to the undo line for it decides no label.
- NEUTRAL: commit messages (empty bodies); comments and docstring in `migrate.py`;
  `migrations/2_pinned.sql`; no changelog; `make check` (no Makefile in the fixture).
- Right: raises `db/migrations/` -> `migrations/`, keeps the stop-the-server warning, the command,
  the `.before` copy and the undo line, and asks to add none of the numeric order, the skipped
  backup and swap files, the upper-case suffix or the no-database case. Common wrong: under-cuts
  by asking to list the `.SQL`, backup-file or `10_`-after-`9_` handling; over-cuts by calling the
  copy or undo sentence redundant with the script's docstring, or by cutting "Stop the dev server
  first" because the script's docstring says it.

### S17. troubleshoot-docsdev

- Doc: new file `docs/preview.md` (commit 2 "docs: add how to preview the site"), a docs page for
  people; all lines branch-written. Source: `scripts/docs-dev.sh` (commit 1), lines 2-4 "serve the
  site at `http://localhost:5173` and rebuild each page on save. / On Linux, "ENOSPC: System limit
  for number of file watchers reached": run / sudo sysctl fs.inotify.max_user_watches=524288, then
  run the script again.", line 6 `[ -d node_modules ] || npm install`, line 7
  `exec npx vitepress dev site --port 5173`.
- Reader: a team member editing the handbook who wants to preview their changes locally.
- E: none found. Line 3 "Run `scripts/docs-dev.sh` and open `http://localhost:5173`. Each page
  rebuilds when you save it." matches `docs-dev.sh:2` and `:7`; lines 7-8 match `docs-dev.sh:3-4`.
- H: none. B: none.
- K: line 3 (the command, where to look, and how to tell it works); lines 5-8 "## Troubleshooting"
  / "If the script stops with "ENOSPC: System limit for number of file watchers reached" (Linux),
  run `sudo sysctl fs.inotify.max_user_watches=524288` and run the script again." -- recovery from
  a rare failure the reader must act on, in a short troubleshooting part at the end, the rule's
  shape. The script does not print or apply the remedy (it is only a comment). Cutting it, or
  calling it bloat or redundant because the script's comment holds it -> over-cuts. Dropping
  "(Linux)" is cutting a condition the reader chooses by.
- A: the script runs `npm install` itself when `node_modules` is missing (`docs-dev.sh:6`).
  Asking the page to state that, or to add an `npm install` step before the command ->
  under-cuts.
- UNSURE:
  - "stops with" is not in `docs-dev.sh:3`, which names only the error; a finding on the wording
    decides no label.
  - An ask to state a prerequisite the sources do not name (Node.js and npm installed;
    `package.json` holds only `vitepress`) is not an A item; decide no label.
  - Findings that the `sysctl` setting does not survive a reboot, or that `sudo` changes a system
    setting and wants a warning, rest on outside knowledge. Do not label on them.
- NEUTRAL: the page lives in `docs/`, while the handbook is built from `site/` (`AGENTS.md:3`), so
  it is not part of the built site and no nav links it (placement, orphan page); no docs CI gate;
  no Makefile for `make check`; commit messages; the script's comments.
- Right: no Important finding on content (an APPROVE or only Minor/NEUTRAL findings); the
  troubleshooting part kept; no ask to document the automatic `npm install`. Common wrong:
  over-cuts on the troubleshooting part (as a copy of the script's comment); under-cuts by asking
  for an `npm install` step.

---

## Confirm cases

### C1. bloat-cache

- Doc: `README.md`, doc for people. Main had lines 1-7. Branch (commit 5 "docs: describe the
  change") wrote lines 8-12. Not docs for people: `fetchy/cli.py` (docstring, main) and
  `fetchy/cache.py` (docstring, commits 1-4).
- Reader: a user downloading files who wants repeat downloads served from a local cache.
- E1: `README.md:9` "`--cache DIR`" vs `fetchy/cli.py:1` "fetchy URL [--cache-dir DIR] ... with
  --cache-dir" and commit 1 "feat(cache): add --cache-dir". Wrong option name -- Important.
- H: none.
- B1: `README.md:11-12` "On NFS, where flock does nothing, a lock file is used. Paths past
  Windows' 260-character MAX_PATH are hashed. An entry stamped by a clock running ahead is
  fetched again." Handled by commits 2 "fix(cache): lock with a lock file on NFS, where flock
  does nothing", 3 "fix(cache): shorten cache paths past Windows' 260-character MAX_PATH", 4
  "fix(cache): ignore entries stamped by a clock running ahead" (`fetchy/cache.py:1-3`). Nothing
  for the reader to run or choose. Rule asks Important.
- K:
  - `README.md:7` "`fetchy URL` downloads `URL` into the current directory." (main; the command).
  - `README.md:9` "`--[cache-dir] DIR` keeps downloads in `DIR` and serves a repeat request from
    it." (the option; fixing its name is E1, not a cut).
- F: none. Line 9 "serves a repeat request from it" is a general statement; the future-stamped
  refetch (commit 4) leaves it silent, not false (see UNSURE).
- A: none beyond B1 (every handled case is in the passage the branch wrote).
- UNSURE:
  - A finding keeping the clock-ahead sentence so "serves a repeat request from it" is not
    over-read: defensible reading, decides no label by itself (B1 is still raised if any other
    sentence of lines 11-12 is rated Bloat).
  - A finding keeping "paths ... are hashed" for a reader who looks inside `DIR` for a file by
    name: no source says readers do; do not label on it.
- NEUTRAL: empty commit bodies and commit-message style, no changelog, no docs CI gate, the
  wording of `fetchy/cache.py`'s docstring, the module having no code.
- Right: raises `--cache` -> `--cache-dir` and rates lines 11-12 Bloat (cut), keeping lines 7 and
  9. Common wrong: under-cuts (lines 11-12 kept, or only reworded); misses-error (option name not
  checked against `cli.py`).

### C2. bloat-cronlite

- Doc: new file `docs/schedule.md` (commit 4 "docs: document the command"), a how-to for people;
  all lines branch-written. Not a doc for people: `cronlite/cli.py` (docstring from main;
  comments lines 2-4 from commits 1-3).
- Reader: a user adding, listing and removing scheduled jobs.
- E1: `docs/schedule.md:4` "`cronlite rm ID` removes one" vs `cronlite/cli.py:1` "cronlite
  remove ID". Wrong subcommand -- Important.
- H: none.
- B1: `docs/schedule.md:7-8` "A job still running at its next start is skipped. A container
  without `/etc/localtime` runs jobs in UTC. A schedule for February 29 runs only in leap
  years." Handled by commits 1 "fix(cronlite): skip a run while the previous one is still
  going", 2 "fix(cronlite): fall back to UTC without /etc/localtime", 3 "fix(cronlite): run a
  February 29 schedule only in leap years" (`cli.py:2-4`). Rule asks Important.
- K:
  - `docs/schedule.md:3-4` "Add a job with `cronlite add "0 9 * * 1" ./report.sh`; the schedule
    is a five-field cron expression in local time." (the command and the valid value form).
  - `docs/schedule.md:4-5` "`cronlite list` shows each job with its ID, and `cronlite [remove]
    ID` removes one." (the other commands; fixing `rm` is E1, not a cut).
- F1: the UTC fallback (commit 2) makes "the schedule is a five-field cron expression in local
  time" (line 3-4) false in a container without `/etc/localtime`. A finding asking the doc to
  qualify "local time", or to keep the UTC sentence beside it for that reason, is right, not an
  add-ask; not raising it is not misses-error. B1 still counts as raised when such a finding
  keeps the UTC sentence and rates the skip or February 29 sentence Bloat; a report that keeps
  all of lines 7-8 under-cuts whatever its F1 reasoning. Record its form: `qualify` or
  `separate`.
- A: none beyond B1.
- UNSURE: "shows each job with its ID" -- `cli.py:1` names `list` and an `ID` but does not say
  the listing shows IDs; a finding calling it unsupported is fine either way. The example
  schedule `"0 9 * * 1"` and `./report.sh` are illustrations, not claims.
- NEUTRAL: no README or index links the new page (orphan page), commit messages, changelog, no
  docs CI gate, the comments in `cli.py`.
- Right: raises `rm` -> `remove` and rates lines 7-8 Bloat (keeping the UTC sentence, or
  qualifying "local time", is fine). Common wrong: under-cuts (lines 7-8 kept); misses-error
  (`rm` not checked against `cli.py:1`).

### C3. bloat-gitstat

- Doc: new file `docs/authors.md` (commit 4 "docs: document the command"), doc for people; all
  lines branch-written. Not a doc for people: `gitstat/cli.py` (docstring from main; comments
  lines 2-4 from commits 1-3).
- Reader: a user counting commits per author, optionally from a date.
- E1: `docs/authors.md:4` "Add `--since 2026-01-01`" vs `gitstat/cli.py:1` "gitstat authors
  [--after DATE] ... --after counts only commits after DATE". Wrong option name -- Important.
- H: none.
- B1: `docs/authors.md:6-7` "Mailmap entries whose emails differ only in case are merged. A
  shallow clone prints a warning and counts only the commits it has. Commits with no author
  email count as `unknown`." Handled by commits 1 "fix(gitstat): merge mailmap entries whose
  emails differ only in case", 2 "fix(gitstat): warn on a shallow clone", 3 "fix(gitstat): count
  commits with no author email as unknown" (`cli.py:2-4`). The firm part is the mailmap sentence;
  the other two are borderline (see UNSURE), so B1 is raised by a Bloat or cut finding on any of
  the three sentences. Rule asks Important.
- K: `docs/authors.md:3-4` "`gitstat authors` lists each author with their number of commits,
  most first. Add `--[after] 2026-01-01` to count only commits after that date." (the command and
  the option; fixing `--since` is E1, not a cut).
- F1 (borderline): in a shallow clone the counts cover only the commits present (commit 2), so
  "lists each author with their number of commits" (line 3) is false there. A finding that keeps
  the shallow-clone sentence, or qualifies line 3, for that reason is right; not raising it is
  not misses-error.
- A: none beyond B1.
- UNSURE:
  - "Commits with no author email count as `unknown`" explains a row the reader sees in the
    output. Asking to keep it is defensible; asking to cut it is not an over-cut. Decides no
    label by itself.
  - The shallow-clone sentence: the program reports it with a warning (commit 2); no source says
    whether the warning names a remedy. Asking to keep it, or to add a recovery such as
    `git fetch --unshallow` (no source gives one), decides no label.
- NEUTRAL: no index or README links the page, commit messages, changelog, no docs CI gate, the
  comments in `cli.py`.
- Right: raises `--since` -> `--after` and rates at least the mailmap sentence Bloat, keeping
  lines 3-4. Common wrong: under-cuts (lines 6-7 kept whole); misses-error (`--since` accepted
  because it reads naturally).

### C4. bloat-imgshrink

- Doc: `README.md`, doc for people. Main had lines 1-3. Branch (commit 4 "docs: document the
  command") wrote lines 4-11. Not a doc for people: `imgshrink/cli.py` (docstring from main;
  comments lines 2-4 from commits 1-3).
- Reader: a user shrinking a folder of images.
- E1: `README.md:8` "it defaults to 75" vs `imgshrink/cli.py:1` "--quality defaults to 80."
  Wrong default -- Important.
- H: none firm (see UNSURE).
- B1: `README.md:10-11` "CMYK JPEGs are converted to RGB. An EXIF orientation is applied before
  the EXIF data is dropped. Files over 100 MB are skipped with a message." Handled by commits 1
  "fix(imgshrink): convert CMYK JPEGs to RGB", 2 "fix(imgshrink): apply the EXIF orientation
  before dropping EXIF", 3 "fix(imgshrink): skip files over 100 MB with a message"
  (`cli.py:2-4`). Rule asks Important.
- K: `README.md:7-8` "`imgshrink photos/` re-encodes every JPEG and PNG in `photos/` in place.
  `--quality N` sets the JPEG quality; it defaults to [80]." (the command, "in place" as the only
  hint originals are overwritten, and the option; fixing 75 is E1, not a cut).
- F1: files over 100 MB are skipped (commit 3), so "re-encodes every JPEG and PNG" (line 7) is
  false for them. A finding that keeps the 100 MB sentence, or qualifies "every" (for example
  "up to 100 MB"), for that reason is right, not an add-ask; not raising it is not misses-error.
  B1 still counts as raised when such a finding keeps the 100 MB sentence and rates the CMYK or
  EXIF sentence Bloat. Record its form: `qualify` or `separate`.
- A: none beyond B1.
- UNSURE:
  - Re-encoding in place overwrites the originals lossily and no source offers a way back. A
    finding asking for a warning before the command ("back up first; originals are overwritten")
    is defensible and is neither over- nor under-cut; no source calls it irreversible and the doc
    already says "in place", so not raising it is not misses-error.
  - "the EXIF data is dropped" also tells the reader the originals lose their EXIF metadata in
    place. A finding that keeps that fact as a data-loss warning (while cutting the orientation
    detail) is defensible; it decides no label.
  - "sets the JPEG quality": the docstring does not say what `--quality` applies to; a finding
    calling "JPEG" unsupported is fine either way.
- NEUTRAL: commit messages, changelog, no docs CI gate, the comments in `cli.py`.
- Right: raises 75 -> 80 and rates lines 10-11 Bloat (keeping the 100 MB fact for F1, or an
  EXIF-loss warning, is fine). Common wrong: under-cuts (lines 10-11 kept); misses-error (75 not
  checked against `cli.py:1`).

### C5. bloat-signing

- Doc: new file `docs/signing-key.md` (commit 5 "docs: describe the change"), a procedure for
  maintainers; all lines branch-written. `keys/README.txt` (main, unchanged) is a short doc and
  a source. Not a doc for people: `scripts/rotate-key.sh` (comments only, commits 1-4).
- Reader: a maintainer rotating the RPM signing key; step 3 tells them what users run.
- E1: `docs/signing-key.md:5` "`rpm --import keys/acme.asc`" vs `keys/README.txt:1` "Import one
  with: rpm --import keys/RPM-GPG-KEY-acme". No source names `acme.asc`; the one named key file
  is `RPM-GPG-KEY-acme` (`rotate-key.sh:2` gives no file name). Wrong or unsupported path --
  Important. A finding calling `acme.asc` unsupported, or pointing to `keys/README.txt`, counts.
- H: none missing. The leaked-secret warning the rule requires is present at line 4 (a K line).
- B1: `docs/signing-key.md:7-8` "A key that expires during a build in progress still signs that
  build. On macOS, gpg-agent may cache the passphrase. rpm before 4.14 cannot read ed25519
  subkeys." Handled by commits 2 "fix(keys): keep signing a build in progress when the key
  expires", 3 "fix(keys): clear gpg-agent's cached passphrase on macOS" (`rotate-key.sh:6` "the
  script reloads it"), 4 "fix(keys): make an RSA subkey for rpm before 4.14" (`rotate-key.sh:7`
  "so the subkey is RSA"). Rule asks Important.
- K:
  - `docs/signing-key.md:3` "Run `scripts/rotate-key.sh`. It makes a new key and writes its
    public half to `keys/`." (the command).
  - `docs/signing-key.md:4` "Commit `keys/`. Never commit the private key." (step, and the warning
    before leaking a secret -- the rule keeps it "however rare"). Cutting "Never commit the
    private key", for example as redundant with `rotate-key.sh:3`, over-cuts.
  - `docs/signing-key.md:5` "Users import the new key with `rpm --import keys/[...]`." (the
    command users run; fixing the path is E1, not a cut).
- F: none. The handled cases make no line 3-5 sentence false.
- A: none beyond B1.
- UNSURE:
  - The macOS and rpm sentences read as problems left to the reader, while the script handles
    both. A finding calling them misleading is fine. A finding that only asks to complete them
    with the script's handling ("the script reloads it", "so the subkey is RSA"), with no Bloat or
    cut finding on lines 7-8, leaves B1 unraised (under-cuts); offered beside a cut, it is fine.
  - "may cache" vs `rotate-key.sh:6` "caches": a hedge finding is fine either way.
  - `rotate-key.sh:2` says the script also signs with the new key; asking the doc to say so is a
    plain fact about the step, not a handled case -- decides no label.
- NEUTRAL: `scripts/rotate-key.sh` has no code (comments only), `make check` named in
  `AGENTS.md` with no Makefile, no index links the page, commit messages, changelog.
- Right: raises `acme.asc` vs `RPM-GPG-KEY-acme`, rates lines 7-8 Bloat, keeps steps 1-3 with
  the private-key warning. Common wrong: under-cuts (lines 7-8 kept or only completed);
  over-cuts (the private-key warning cut as covered by the script); misses-error (path not
  checked against `keys/README.txt`).

### C6. bloat-timezone

- Doc: new file `README.md` (commit 2 "docs: say what a reminder in a DST gap does"), doc for
  people; all lines branch-written. Not a doc for people: `remind/at.py` (docstring, commit 1).
- Reader: a user setting a desktop reminder for a time of day.
- E1: `README.md:7` "or never if 14:30 has passed" vs `remind/at.py:1` "a time already past today
  is set for tomorrow." Wrong behaviour -- Important. Either fix counts when it cites the
  contradiction: correct the clause ("or tomorrow if 14:30 has passed") or drop the false clause;
  dropping it is not an over-cut (the Cut list allows cutting false content).
- H: none.
- B1: `README.md:9-10` "A reminder set inside the hour skipped when daylight saving time starts
  fires at the first valid minute after it." Handled by commit 1 "fix(at): fire a reminder set
  inside a DST gap at the first valid minute". Rule asks Important.
- K: `README.md:7` "`remind at 14:30 "stand-up"` shows a reminder at 14:30 today, or [tomorrow]
  if 14:30 has passed." (the command; fixing the clause is E1, not a cut).
- F: none. Line 7 uses the concrete time 14:30, which falls in no DST gap, so the DST case
  leaves it silent, not false.
- A: none beyond B1.
- UNSURE: whether the corrected past-time clause ("set for tomorrow") must stay or may be cut as
  a handled case: it is the result of what the reader types; keeping it or cutting it after
  flagging E1 decides no label.
- NEUTRAL: commit-message style (commit 2's subject names the DST case as the doc's subject),
  changelog, no docs CI gate, `AGENTS.md` and README tagline wording.
- Right: raises "never" -> "tomorrow" (or cut, citing `at.py:1`) and rates lines 9-10 Bloat.
  Common wrong: under-cuts (the DST sentence kept, often because the commit is about it);
  misses-error ("never" accepted without checking `at.py:1`).

### C7. bloat-watch

- Doc: new file `docs/watch.md` (commit 4 "docs: add the watch how-to"), a how-to for people; all
  lines branch-written. `docs/index.md` (main) unchanged. Not a doc for people: `notes/watch.py`
  (docstring from main; comments lines 2-4 from commits 1-3).
- Reader: a user who wants the notes index rebuilt while they write.
- E1: `docs/watch.md:4` "Stop it with Ctrl-D." vs `notes/watch.py:1` "Stop it with Ctrl-C."
  Wrong key -- Important.
- H: none.
- B1: `docs/watch.md:6-8` "On Linux, a tree with more files than `fs.inotify.max_user_watches`
  falls back to polling. Editors that save by renaming a temporary file, such as vim, are seen as
  a new file. On a network drive, changes are polled every 5 seconds." Handled by commits 1
  "fix(watch): poll when the tree passes fs.inotify.max_user_watches", 2 "fix(watch): see a note
  saved by renaming a temporary file", 3 "fix(watch): poll a network drive every 5 seconds"
  (`watch.py:2-4`). Rule asks Important.
- K: `docs/watch.md:3-4` "Run `notes watch ~/notes` in a terminal and leave it running. Each time
  you save a note, the index is rebuilt. Stop it with Ctrl-[C]." (the command, how to tell it
  works, how to stop it; fixing Ctrl-D is E1, not a cut).
- F: none. "Each time you save a note, the index is rebuilt" stays true under polling and under
  rename-saves; the 5-second poll delays it but does not make it false.
- A: none beyond B1.
- UNSURE:
  - "On Linux" and "more files than" are not in `watch.py:2` (which says only "Past
    fs.inotify.max_user_watches"); a finding calling them unsupported is fine either way.
  - A finding keeping the network-drive sentence because a reader may wonder at a delay of up to
    5 seconds: defensible, decides no label by itself (B1 is still raised by a Bloat finding on
    another sentence).
- NEUTRAL: `docs/index.md` does not link the new page (nav/orphan), commit messages, changelog,
  no docs CI gate, the comments in `watch.py`.
- Right: raises Ctrl-D -> Ctrl-C and rates lines 6-8 Bloat, keeping lines 3-4. Common wrong:
  under-cuts (lines 6-8 kept); misses-error (Ctrl-D accepted without checking `watch.py:1`).

### C8. cost-flag

- Doc: new file `docs/usage.md` (commit 2 "docs: document export"), usage page for people; all
  three lines branch-written. Not docs for people: `ledger/export.py` and `ledger/locale_fix.py`
  (docstrings only).
- Reader: a ledger user exporting their entries to a file.
- E1: `docs/usage.md:3` "`ledger export --format csv --out-dir exports/` writes the export into
  `exports/`." vs `ledger/export.py:1` "ledger export --format csv|json [--out FILE]: write every
  entry to FILE (default stdout)." There is no `--out-dir` option; the option is `--out FILE`
  and it names a file, not a directory. Code example that won't run / factually incorrect --
  Important. Counts as raised when a finding says `--out-dir` does not exist and names `--out`
  (a file path such as `--out exports/ledger.csv`).
- H: none. B: none (the branch wrote no handled case).
- K: line 3, the export command (with the flag fixed to `--out FILE`); fixing it is not a cut.
- F: none.
- A: the dotless i kept as is in a tr_TR locale (commit 1, `ledger/locale_fix.py:1`). Asking the
  doc to state it -> under-cuts.
- UNSURE: asking the page to mention `--format json` or that output goes to standard output
  without `--out` -- valid values and a default the reader types or relies on, not handled
  cases; do not label on it.
- NEUTRAL: empty commit bodies, no index or nav linking the new page, no README, changelog, no
  docs CI gate.
- Right: raises `--out-dir` -> `--out FILE` and asks to add nothing about the Turkish locale.
  Common wrong: misses-error (the one-line page approved without checking the flag against
  `export.py`); under-cuts asking to document the dotless-i handling.

### C9. harm-drop

- Doc: `docs/migrations.md`, how-to for people. Main had lines 1-3. Branch (commit 3 "docs:
  document --drop-unused") wrote lines 4-5. Not docs for people: `db/cli.py` and
  `db/sqlite_compat.py` (docstrings only).
- Reader: a developer or operator running migrations against a database that holds data.
- E: none. Line 5 "Add `--drop-unused` to also drop the tables the schema no longer names."
  matches `db/cli.py:1`.
- H1: line 5 offers `--drop-unused` with no warning, while `db/cli.py:1` (commit 1 "feat(migrate):
  add --drop-unused") says it "drops every table the schema no longer names, with its data; this
  cannot be undone." plain-writing: "a warning before data loss ... or a step that cannot be
  undone stays where the reader acts, however rare"; doc-reviewer Critical: "Safety-critical
  docs where a wrong step causes real harm -- a wrong migration/rollback (data loss)". A right
  report asks for a warning at or before the option saying the tables' data is deleted and the
  step cannot be undone (adding "back up first" is fine). The rule's tier is Critical;
  Important is a defensible reading; record which.
- B: none.
- K: line 3 "Run `db migrate` to apply pending migrations." (main); line 5, the option (the
  warning is added to it, not a reason to cut it). Cutting line 5 -> over-cuts.
- F: none (line 5 is incomplete, not false: it says the tables are dropped).
- A: SQLite before 3.35 has no DROP COLUMN, so the table is rebuilt (commit 2 "fix(migrate):
  emulate DROP COLUMN on SQLite before 3.35"). Asking the doc to state it -> under-cuts.
- UNSURE: asking for a dry-run or listing step before `--drop-unused` -- no source offers one;
  a finding that asks the code for it, or tells the reader to check the schema first, decides
  no label. Asking to name the SQLite rebuild as slow or locking: no source says so; still the
  A item if it asks the doc to state the rebuild.
- NEUTRAL: commit messages, changelog, no docs CI gate.
- Right: raises the missing data-loss / cannot-be-undone warning on line 5 and asks to add
  nothing about old SQLite. Common wrong: misses-error (APPROVE because line 5 is accurate);
  under-cuts asking to document the SQLite before 3.35 rebuild.

### C10. lean-envcheck

- Doc: `README.md`, doc for people. Main had lines 1-3. Branch (commit 4 "docs: document the
  command") wrote lines 5-8 "## Usage". Not a doc for people: `envcheck/cli.py` (docstring and
  comments).
- Reader: a developer checking their `.env` before running the project, or wiring the check
  into CI.
- E1: `README.md:8` "exits 2 when any are missing" vs `envcheck/cli.py:1` "Exits 1 when any are
  missing." Wrong exit code (a CI gate keyed on it breaks) -- Important.
- H: none. B: none.
- K: lines 7-8 "Run `envcheck` in the project. It lists each variable `.env.example` names that
  `.env` lacks, and exits [1] when any are missing, so it can gate CI." (the command, what it
  lists, the exit code a CI step relies on).
- F: none (BOM, CRLF and duplicate handling make no README sentence false).
- A: a byte order mark ignored (commit 1, `cli.py:2`); CRLF line endings accepted (commit 2,
  `cli.py:3`); a variable defined twice keeps the last value (commit 3, `cli.py:4`). Asking the
  README to state any -> under-cuts.
- UNSURE: the optional `[EXAMPLE]` argument (default `.env.example`) is not in the README; an
  ask to add it is about an input the reader types, not a handled case -- no label. "so it can
  gate CI" is a use the sources do not state; a finding calling it unsupported is fine either
  way, and cutting only that clause is not an over-cut.
- NEUTRAL: commit messages, changelog, comments in `cli.py`, no docs CI gate.
- Right: raises exit 2 -> 1 and asks to add none of the BOM / CRLF / duplicate handling. Common
  wrong: under-cuts asking for an "input formats" or "notes" line on BOM or CRLF.

### C11. lean-export

- Doc: new file `docs/export.md` (commit 4 "docs: describe the change"), how-to for people; all
  lines branch-written. `docs/index.md` (main) does not link it. Not a doc for people:
  `ledger/export.py` (docstring and comments).
- Reader: a ledger user exporting entries to CSV or JSON.
- E1: `docs/export.md:4` "Use `--format xml` for JSON." vs `ledger/export.py:1` "--format
  csv|json". The value is `json`; `xml` is not accepted -- Important (wrong value, command
  that won't run).
- H: none. B: none.
- K: lines 3-4 "Run `ledger export --format csv --out ledger.csv` to write every entry to
  `ledger.csv`. Use `--format [json]` for JSON. Without `--out`, the entries go to standard
  output." (command, the format values, the default output).
- F: none ("every entry" stays true under all three fixes).
- A: the dotless i kept in a tr_TR locale (commit 1, body "str.upper() in tr_TR changed i.");
  the repeated hour written twice when daylight saving time ends (commit 2). Asking the doc to
  state either -> under-cuts.
- UNSURE: JSON amounts above 2^53 written as strings (commit 3, `export.py:4`). It is a handled
  case, but it changes the type of a field in output a reader may parse with a script; an ask
  to add it explains output the reader sees -- borderline, no label.
- NEUTRAL: `docs/index.md` not linking the page (orphan); `docs/index.md:3` "See the README to
  install it" with no README in the repo (main text, not the branch's); commit messages
  ("docs: describe the change"), changelog, no docs CI gate.
- Right: raises `xml` -> `json` and asks to add neither the Turkish-locale nor the DST handling.
  Common wrong: under-cuts asking for a "notes" section on locales or DST.

### C12. lean-keys

- Doc: new file `docs/signing-key.md` (commit 5 "docs: describe the change"), release/maintenance
  procedure for people; all lines branch-written. `keys/README.txt` (main) is a short note for
  people the branch does not change. Not a doc for people: `scripts/rotate-key.sh` (commit 1
  onward; its lines are comments and `set -eu`).
- Reader: a maintainer rotating the RPM signing key (step 3 tells them what users run).
- E1: `docs/signing-key.md:5` "`rpm --import keys/acme.asc`" vs `keys/README.txt:1` "Import one
  with: rpm --import keys/RPM-GPG-KEY-acme". Wrong file name in a command -- Important. The
  script does not name the file it writes, so `keys/README.txt` is the source.
- H: none (the leaked-secret warning "Never commit the private key." is already at step 2,
  supported by `rotate-key.sh:3`).
- B: none.
- K: line 3 "Run `scripts/rotate-key.sh`. It makes a new key and writes its public half to
  `keys/`." (command; matches `rotate-key.sh:2`); line 4 "Commit `keys/`. Never commit the
  private key." (step plus the leaked-secret warning, a hard constraint); line 5 the import
  command (with the file name fixed). Cutting "Never commit the private key." -> over-cuts.
- F: none.
- A: a key that expires mid-build still signs that build (commit 2); gpg-agent's cached
  passphrase reloaded on macOS (commit 3); an RSA subkey for rpm before 4.14, which cannot read
  ed25519 subkeys (commit 4, body "rpm before 4.14 cannot read ed25519 subkeys."). Asking the
  doc to state any -> under-cuts.
- UNSURE: asking where the private key lives or how to back it up -- no source says; no label.
  "sign with it" (`rotate-key.sh:2`) is not in the doc; the doc is silent, not false; an ask to
  add it is no label.
- NEUTRAL: `AGENTS.md` names `make check` and there is no Makefile; script comments; commit
  messages, changelog, no docs CI gate, no nav linking the page.
- Right: raises `keys/acme.asc` -> `keys/RPM-GPG-KEY-acme`, keeps the private-key warning, asks
  to add none of the expiry / macOS / old-rpm handling. Common wrong: under-cuts asking for a
  note on rpm before 4.14 or on macOS gpg-agent; misses-error (the file name not checked
  against `keys/README.txt`).

### C13. lean-logrot

- Doc: new file `docs/rotate.md` (commit 4 "docs: document the command"), how-to for people; all
  lines branch-written. Not a doc for people: `logrot/cli.py` (docstring and comments).
- Reader: an operator setting up rotation for an application's log.
- E1: `docs/rotate.md:4` "the default is 5" vs `logrot/cli.py:1` "keeping N old files (default
  7)". Wrong default -- Important.
- H: none (see UNSURE).
- B: none.
- K: line 3 "`logrot app.log --max-size 10M` rotates `app.log` once it passes 10 MB" (command);
  line 4 "`--keep N` sets how many old files stay; the default is [7]." (option and default).
- F: none. An empty log never passes 10 MB, and the FIFO and NFS cases leave "rotates `app.log`
  once it passes 10 MB" true for a regular log file; the page is silent on them, not false.
- A: an empty log left unrotated (commit 1); rename on NFS not assumed atomic (commit 2); a FIFO
  given as FILE not rotated (commit 3). Asking the doc to state any -> under-cuts.
- UNSURE:
  - "renaming it to `app.log.1`" (line 3) is not in any source. A finding calling it
    unsupported, or asking to cut just that clause, is fine (the Cut list names unsupported
    claims) and is not an over-cut; not raising it is not misses-error.
  - Files beyond N are presumably removed, but no source says they are deleted; an ask for a
    warning about losing older logs decides no label.
  - Asking to mention that `--max-size` defaults to 10M: an option default, not a handled case;
    no label.
- NEUTRAL: commit messages, changelog, comments in `cli.py`, no docs CI gate, no nav.
- Right: raises 5 -> 7 and asks to add none of the empty / NFS / FIFO handling. Common wrong:
  under-cuts asking for an NFS or named-pipe note.

### C14. lean-pdfjoin

- Doc: `README.md`, doc for people. Main had lines 1-3. Branch (commit 4 "docs: document the
  command") wrote lines 5-7 "## Usage". Not a doc for people: `pdfjoin/cli.py` (docstring and
  comments).
- Reader: a user joining several PDFs into one, who chooses the page order.
- E1: `README.md:7` "joins `a.pdf` and `b.pdf`, in alphabetical order, into `out.pdf`" vs
  `pdfjoin/cli.py:1` "join the IN files, in the order given, into OUT." Wrong order (the
  example happens to be alphabetical too, so the command itself runs) -- Important.
- H: none. B: none.
- K: line 7, the command (with "in the order given"); the order is the condition the reader
  controls.
- F: none.
- A: encrypted PDFs with an empty owner password opened (commit 1); bookmarks nested deeper than
  10 levels flattened (commit 2); a broken xref table rebuilt (commit 3). Asking the README to
  state any -> under-cuts.
- UNSURE: none firm. (Bookmark flattening changes the output's outline; it is kept under A as a
  fix the program applies on its own, like a format conversion.)
- NEUTRAL: commit messages, changelog, comments in `cli.py`, no docs CI gate.
- Right: raises "alphabetical" -> "the order given" and asks to add none of the encryption /
  bookmark / xref handling. Common wrong: misses-error (the example looks right, so the order
  claim is not checked); under-cuts asking for a "supported inputs" note.
