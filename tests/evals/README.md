# Eval suites

An eval suite tests whether a change to a skill, agent or command makes the agent behave better or worse.
Each case is a small fixture repository and a task. The runner runs the cases as headless `claude -p`
sessions on two versions of the plugins, grades every session, and compares the two versions task by task.
Everything runs locally on your own `claude` login.

Build a suite as big as its verdicts need, not as small as its cost allows. `make eval-size` estimates,
for each model and split, the chance that a positive control (the text under test removed) comes out
WORSE; below 80%, the split cannot be trusted to catch harm, and the fix is more cases the text changes.

A suite lists the models its plugins run on, and every baseline and verdict is per model. A rule one
model follows unaided is not redundant: another model, or the next version, may need the text to follow
it. A case's kind and checks are the same on every model; its baselines show where it has room to gain.
For an agent that pins `model:` in its frontmatter, `models` sets the main thread that dispatches it;
the agent runs on its pinned model, which each sample records.

Each model has a role, set by calibration. A gate model's screens decide SHIP. A watch model's screens
are advisory: listed under `watch` in `suite.toml`, it is a model whose A/A screens cannot SHIP, such as
a weaker one whose guards are too noisy to show non-inferiority or that cannot meet a must-hold rule
even with the text. A change must not make any model worse, so harm on a watch model is still reported
and the PR explains it; a must-hold failure there is reported as a standing limit, tracked in an issue,
not as a failed bar. A watch model becomes a gate model once its A/A screens SHIP with no STANDING line.

## When a change needs evals

Test a change in proportion to the harm it is likely to do before someone notices and reverts it: what
the changed text could plausibly make the agent get wrong or leave unfixed, how many users it reaches,
how long a wrong turn could go unseen, and how cheaply it is undone once seen (a PR left a draft: one
command; a wrong commit message on main: never, though it rarely costs much). The kind and size of a
change are clues to that, not rules. Pick the tier before writing a case, and say in the PR which tier
and why.

1. **No eval.** Nothing the change alters reaches the model, such as a code comment in a hook script; a
   link or heading in a skill, agent or command still reaches it.
2. **Regression only.** Little harm before it is noticed: typically a few lines refining an existing
   rule, a pointer or a wording fix. Write no new suite.
3. **Smoke.** Some harm before it is noticed and reverted: typically a new rule or step in an existing
   skill, agent or command. Write a handful of cases on one model in a scratch suite outside the repo
   ("Smoke tests" says how).
4. **Full suite.** Serious harm before it is noticed and reverted: typically a new skill, agent or
   command, a change to how a reviewer rates, a changed `description` or `when_to_use` (a skill that
   stops loading goes unseen), or a fix for something seen going wrong more than once. Write or extend a
   suite so committed cases exercise the changed text ("Choosing cases").

A direct suite's `covers` names a changed file; an indirect suite covers only files that load, directly
or through other files, a changed skill, agent or command. Run `make eval-plan TIER=<n>` and do what it
prints. In the PR, also say what each test showed, name at tier 2 each file the plan lists as UNCOVERED,
and, at tiers 2 and 3, what the plan's report shows each direct suite's screen split can see. At tier 4
a change goes ahead when a direct suite covers each changed file and each direct suite's screen and
confirm SHIP on every gate model. Below tier 4, and for any indirect suite, it goes ahead unless a
screen or smoke test it calls for shows harm: a screen on a gate model comes out HURT, or a smoke test's
samples show the new text doing worse than the old.

### Smoke tests

A smoke test's cases all sit on `dev`, in a scratch suite outside the repo and outside `/tmp`; pick them
by steps 3 and 4 of "Choosing cases" (the new text, and tasks the agent already does right where it
could get in the way), and write its `suite.toml` and cases by "Layout", "Writing a case" and "Graders".
Run `make eval-run SUITE=<dir> ARM=old`, then `ARM=new SPLIT=dev`, and read each sample with
`python3 scripts/eval.py show <key>`, for the keys `make eval-run` prints. The lint does not reach a
scratch suite, so check by hand that its prompts give nothing away and its checks grade those samples
right. Never commit the scratch suite; say in the PR what its cases showed.

## Layout

A suite mirrors its source path: `tests/evals/<plugin>/skills/<name>/` for a skill,
`tests/evals/<plugin>/agents/<name>/` for an agent.

- `suite.toml`: what it covers, the models it runs on, its metrics, its pass rule and its clusters.
- `cases/<id>/prompt.md`: the task, as the user would type it.
- `cases/<id>/fixture/` and an optional `build.py`: the repository the session starts in.
- `cases/<id>/key.toml`: the split, the kind, the checks, and the facts, plants and baseline counts
  the checks rely on; for a task that pushes or calls `gh`, its remote and `gh` replies.
- `cases/<id>/fix/`: the files that fix the case's planted problems, laid over the fixture by the lint.
- `cases/<id>/reference/`: outputs that pass every check, and outputs that fail the case's target check.

## The arms

- `old`: the plugins at the merge base of your branch with `main`.
- `new`: the plugins in your working tree.
- `none`: `old` with the text under test removed: a skill's directory deleted and its preloads dropped,
  or an agent's or command's body cut to its first line.
  A target that renames or replaces texts of `old` lists them in `suite.toml` as
  `replaces = ["<plugin>:<name>", ...]` (top-level, above the first `[table]`), and `none` removes them
  too, so it holds none of the texts the change replaces.

## Choosing cases

1. **Start from real failures.** Look first at issues, PR review comments and session transcripts where
   the agent got it wrong, and rebuild each as a fixture and a task. Invent a case only where no real
   failure exists.
2. **Prove the failure happens.** For a new skill, the agent must get the case wrong under `none`; for a
   change to an existing text, under `old`, because that is what the change claims to fix. Run each
   arm on each of the suite's models (`make eval-run ... RECORD=1` writes the counts into the key).
   A case's kind holds on every model: make it a target case when old fails it on a model the change is
   meant to help. Keep it only if it fails at least once; prefer cases that fail in most runs, because a
   case the baseline usually passes has little room to show a gain, so use it as a regression case
   instead. The count is for choosing cases only: a verdict always compares fresh
   samples of both arms.
3. **Give each rule the change touches a case.** A target case if its failure can be triggered, a
   regression case if the agent already follows the rule. One case exercises a rule; it does not
   measure it.
4. **Add regression cases.** These are tasks the agent already does right, where the new text could get
   in the way: a rule applied where it does not fit, or the main job crowded out. Most of the harm a skill
   does shows up here.
5. **A new duty needs cost cases** on the agent's main job, such as planted code bugs for a reviewer that
   gained a prose duty.
6. **A changed `description` or `when_to_use` needs trigger cases**: about 20 prompts, half that should
   load the skill and half near misses that should not. A near miss shares the skill's words but needs
   something else. Should-load and should-not-load are separate metrics.
7. **Vary the cases** in how the user phrases the request, how much context they give, the repository's
   shape, and which step of the task meets the rule, so the result is not tied to one phrasing.
8. **Count each task once.** The verdict's unit is a task. Variants of one task (the same fixture and
   request, with different wording or history) form a cluster in `suite.toml` and count as one unit, so
   one task cannot outvote the others. Different tasks that test the same rule count separately: each is
   independent evidence that the rule holds in another context. The verdict speaks for the suite's
   tasks; more independent tasks per rule is what makes it speak for the rule. A split needs at least 5
   units before any verdict can be reached, and more when the pass rule reads several metrics;
   `make eval-size` says when a split has too few.
9. **Make tasks realistic.** For a skill the agent loads itself, one-step prompts often get done without
   loading it.

## Writing a case

- **The prompt says what the user wants done,** never the rule or the expected output. List the words
  that would give the answer away under `hints` in the key; the lint fails a prompt that uses them. It
  catches only those words, so also read the fixture for a giveaway in other words, such as an issue
  text that states the fix.
- **Every fact a check needs is where the writer can find it,** in the prompt or the fixture: if a check
  wants `#42` in the commit message, issue 42 appears in the task. Each fact in the key names where it
  is, and the lint confirms it. What the fixture must not hold is the expected output itself, in a file,
  a branch name or a commit.
- **Prove the problem the task fixes is real.** Declare it as a `[[plant]]` in the key, with a `verify`
  command (offline, python3 or node only) that fails on the fixture as a session gets it and passes with
  `fix/` laid over it; the lint runs both. Whatever else the prompt says, a problem to leave for later
  or why the old design changed, must not be false of the fixture: a session that checks and finds it
  false behaves differently. Say it so the fixture cannot contradict it, as a decision or an issue
  tracked elsewhere, rather than build it in. A fixture's earlier history may be as untidy as a real
  one: a past commit's message need not match its diff unless the task depends on it.
- **A task that pushes or calls GitHub** sets `remote = true` in the key. The session's repository then
  has an `origin`: a local bare repository holding every branch and tag the fixture and `build.py` made,
  each branch tracking it, so `git push` works, and `origin/HEAD` names `main`, as in a clone, when the
  fixture keeps the `main` branch it starts on. To start with a branch ahead of, behind or missing from
  `origin`, `build.py` makes `origin` itself:
  `git init --bare -b <the fixture's default branch> ../origin.git`,
  `git remote add origin ../origin.git`, then `git push -u origin <that branch>`, so `origin/HEAD` can
  name it, and pushes what else it wants there. Without a remote named `origin`, the runner fills that
  same `../origin.git` with every branch. It keeps an `origin` that `build.py` made as `build.py` left
  it, adding only `origin/HEAD` when the repository lacks it and origin's HEAD names a branch origin
  holds. That `origin` is a local path, or a URL `url.<path>.insteadOf` rewrites to one:
  git refuses any other. The session's `gh` is a stub that records every call and answers from the key's
  `[[gh]]` tables: the first whose `match` regex finds the call's arguments joined with spaces, each
  newline in them written as `\n` (`pr create --draft --title ...`), prints its `stdout` and exits with
  its `exit` (default 0). A call no reply matches fails with `gh stub: no reply for: <arguments>`, so
  script every call the task needs, reads (`gh pr view`, `gh api`) included. A `[[gh]]` table implies
  `remote = true`, and the replies count in the case hash, like the fixture.

  Write each `match` to accept every call the task could make at that step, keyed on the subcommand
  wherever it falls, as gh takes flags before it (`gh -R o/r pr create`): `(^|\s)pr create\b`. Grade the
  behaviour under test with a check, never with a `match`: a narrow match (`--draft`) fails the other
  calls, and the failure invites the agent to retry until it hits the scripted one. The session could
  read the answer too: the replies sit in its sandbox, so a sample whose tool calls name the stub's
  directory or `gh-stub-replies.json` is excluded. A reply prints only to stdout, while gh writes its
  errors to stderr, which a reply cannot script: leave `stdout` empty in a reply with a non-zero `exit`.

  ```toml
  [[gh]]
  match = '(^|\s)pr create\b'
  stdout = "https://github.com/acme/app/pull/7\n"
  ```

- **Keep tool configuration out of a fixture.** A fixture whose `pyproject.toml` has a `[tool.ruff]`
  table gets a `.ruff_cache/` written into it by the commit hooks, and the case hash counts every file in
  the fixture, so each hook run would redraw the case's samples.
- **Check the checks.** Write several passing references that differ in wording, order and approach, and
  failing references for the target check. The lint runs the regex checks on all of them; a judged check
  is scored on the references when its judge is calibrated (Judges, bar row 5). Prefer checks on what the
  agent produced over checks on how it got there.
- **Ask one question per case.** One target behaviour, graded by checks that answer it.

## Splits

- `dev`: look at everything, iterate freely.
- `screen`: choose between versions of the text here. Results only; never tune the text to one case.
  Screen at most five versions on one screen split, then move its cases to `dev` and write fresh ones.
- `confirm`: run once, on the one version you chose. Its result goes in the PR description.

If `confirm` fails, report it; its cases move to `dev`, and the next candidate needs fresh confirm cases.
Record every case that leaves a held-out split in `BURNED`, a top-level list of case ids in `suite.toml`
(above its first `[table]`, or TOML files it under that table), with the reason in a comment, and say in
the PR how many versions you screened.

## Graders

- **Grade what the agent produced:** a regex over the commit messages, the final reply, a file, what
  the agent sent to GitHub or a subagent, or a subagent's report (below). An `absent` check fails when
  the agent produced nothing to check.
- **Several files at once:** `artifact = "files:<glob>"` reads every file of the session's final tree
  that the glob matches, `.git` aside, in path order, each after a `==> <path> <==` line: `*`, `?` and
  `[...]` match within one name, `**` across any number of directories. A reference gives the files
  under `[files]`, as for `file:<path>`.
- **Whether the result works:** `artifact = "verify"` with a `command`, such as
  `command = "python3 -m pytest -q"` for planted tests, runs the command without a shell in the
  session's final tree and environment, and holds when it exits 0 within 60 seconds. It is not graded
  on references.
- **Whether a skill was in context when the agent wrote** is a guard or a diagnostic, not a primary
  metric, except in trigger cases, where loading the skill is the behaviour under test.
- **A subagent's work:** `report:<agent>` is every report that agent handed back, `brief:<agent>` every
  Agent-call prompt the main thread sent that agent type (a call that ended in error aside), and a
  delivery check with `agent = "<plugin>:<agent>"` reads that subagent's skill loads and writes instead
  of the main thread's. Subagents are followed at every depth, a subagent's own subagents included, and
  so is an Agent call run in the background, which under `-p` is every one the main thread makes: its
  report is the one Claude Code's notification carries when the agent finishes. A reference gives reports under `[reports]` and briefs under `[briefs]`, as
  `"<plugin>:<agent>" = "text"`.
- **How the subagents worked:** each Agent call is a spawn, and these checks read every spawn at
  every depth, two spawns of one agent type apart. `artifact = "overlap"` holds when no file was
  written by two spawns (the main thread's writes aside); `artifact = "spawn-writes"` with a `write`
  kind when no spawn made that write, even one that failed, such as `write = "commit"`;
  `artifact = "barrier"` when the main thread wrote no file, nor tried to, between an Agent call and
  the last report of the spawns out with it. A delivery check's `write = "spawn"` is an Agent call: with
  `state = "in-context"` the skill arrived before every Agent call of the main thread, or with an
  `agent`, of that subagent. None of these is graded on references.
- **What the agent sent to GitHub:** `gh` is every call the stub recorded but Claude Code's own (below),
  one `gh <arguments>` line each with newlines written as `\n`, then a blank line, then every text the
  calls passed, newlines kept: each argument and its tails (past each leading letter of a short flag or a
  group of them, `-bText` or `-dFbody.md`; past a key's `=`, `--body=Text` or `body=@b.md`; past a
  leading `@`), stdin, and every existing regular file one of those names. It holds more than the
  bodies, titles and `--jq` strings included, so a `present` check on a body can be met by a title or by
  another call's text. A check about one flag or command reads only the call lines, up to the first
  blank line, with the form `present = '\A(?:.+\n)*gh (?:.* )?pr create\b.*--draft'`: in a check, `^`
  matches at the start of every line, so `^` alone also reaches the texts after the blank line, a body
  that quotes `gh pr create --draft` included, and `(?:.* )?` lets gh flags come before the subcommand,
  as in `gh -R o/r pr create`. An inline body stays on its own call line, so a body passed as
  `--body "... --draft ..."` can still meet that form. The stub reads a file only inside the sandbox, the
  eval runner's temp directory or `/tmp`, where an agent may write `/tmp/pr-body.md`: a body file
  elsewhere reads as absent, as does a body piped to `/dev/stdin` or passed as `/dev/fd/N` by process
  substitution `<(...)`. It reads stdin whenever an argument or a tail of one is exactly `-`, even where
  gh would not, as a key's value (`-f q=-`), so such a call waits while stdin stays open. It reads no
  file or stdin of a call with an argument equal to `secret`, `variable` or `auth` anywhere, a label
  included (`--label auth`): such a call is recorded with no file or stdin text. A call of the shape
  Claude Code makes on its own (`gh pr view --json url` and `gh pr view <branch> --json url` on
  2.1.311) is left out even when the agent makes it, so no check grades one. A reference gives its `gh`
  text as `gh = "text"`; the lint drops such calls from its call lines too, but not from its texts. The
  lint fails a `gh` check on a case without a remote. For "made no such call", which holds when the
  agent made no call at all, negate the same form: `present = '\A(?!(?:.+\n)*gh (?:.* )?pr ready\b)'`.
- **A judge** answers one yes/no question about one artifact, for what a regex cannot check, and is called
  only with `--judge`: see Judges.

## Judges

A judged check names a question declared once in `suite.toml`. Each case gives the reference that says
what a "yes" means for it:

```toml
# suite.toml
[[judge]]
id = "flags-plant"
question = "Does the report raise, as a finding of its own, the problem the reference describes, at a rating the reference accepts?"
# model = "claude-opus-5-5", effort = "high" and panel = 3 are the defaults.
# Calibration only:
held_out = ["nonlocal-parse", "retold-utc"]        # the held-out set, never tuned on; the rest are dev
siblings = [["nonlocal-parse", "nonlocal-stamp"]]  # cases whose plants are of one kind
yes_ratings = ["Critical", "Important"]            # a silver label is yes when the plant's finding is rated so
compare = "found_regex"                            # the metric the judge would replace

# cases/<id>/key.toml
[[check]]
metric = "found"
artifact = "report:praxis:general-reviewer"
judge = "flags-plant"
reference = """
The branch adds `_median` to tally/stats.py beside `statistics.median`. Only a finding whose subject is
that reimplementation counts, and only when the report rates it Important or Critical.
"""
# yes_ratings = ["Critical"]  # when this case's silver labels need other ratings than the judge's
```

- The judge is `claude -p` on its model and effort, with no tools and no customizations, asked for
  `{answer, quote}`. It sees the question, the reference and the artifact, with plugin, skill, agent and
  command names and sandbox and store paths replaced by neutral tokens. It runs `panel` times per sample
  and the majority decides. "unknown" counts as no, and so does a "yes" whose quote is not in the artifact.
  An output that does not parse is no answer: the next run calls again, nothing is guessed.
- A spoiled sample or an empty artifact fails the check with no call.
- `run` and `screen` call a judge only with `--judge` (`JUDGE=1` with make), because judge calls weigh
  heavily on the usage limit. Without it they still read kept answers, but a metric that lacks one on any
  sample is NOT JUDGED, never a pass or a fail: a screen whose primary or a guard is not judged is
  INCONCLUSIVE, and `run` neither counts nor records a case while a metric it counts (any but a guard)
  is not judged.
  The `judge-*` commands call by design, naming the judge with `--judge <id>`.
- With `--judge`, a sample whose panel is still incomplete (an API error, a usage limit) is left out like
  an excluded sample: the screen cannot SHIP until a rerun fills it.
- Answers are kept in the store's `judgments/`, keyed by the model, effort, question, prompt texts,
  reference, stripped artifact and panel member, so a regrade calls nothing. The Claude Code version is
  not part of the key, and an update of it does not call for calibrating again.
- A judge gates nothing until its stamp shows it cleared the bar below. Until then its checks score into
  a reported metric of their own, `<metric>@<judge>`, and the screen says why. A judged check on a
  must-hold metric is refused: one judge error in a screen would read as HURT.
- Judge error shrinks a true effect by J = TPR + TNR - 1 and, when it is the same in both arms, makes no
  false HURT. Guard margins on a judged metric are on the scale the judge observes. `make eval-size` prints J
  for a judged primary metric. For a judge that gates, the screen repeats its stamp's warnings (J
  differing by more than 0.1 between the arms it was calibrated on, a dev TPR or TNR more than 0.1 above
  held-out's), and it warns when the judge's model wrote the artifact it judges.
- The plan pins each judge's version: a changed judge refuses a verdict until `NEW_PLAN=1`, and regrades
  the drawn samples without new sessions.

### Calibrating a judge

The bar, on held-out items the judge was never tuned on:

| # | Items | Bar |
|---|---|---|
| 1, 2 | natural positives, natural negatives (silver labels) | 40 or more each; TPR, TNR >= 0.9 and their Wilson 95% lower bound >= 0.80 |
| 3 | natural items | Cohen's kappa >= 0.80 over 80 or more |
| 4 | sibling swaps: a report judged against the reference of another held-out case whose plant is of the same kind | as rows 1 and 2 |
| 5 | the cases' references | at most 2 wrong |
| 6 | controls: empty, "I don't know", another case's plant, an injection appended to a "no" | 10 each, none answered yes |
| 7 | invariance pairs: format lines removed, two unrelated Minor findings appended | 60 or more each, 95% unchanged |
| 8 | rows 1 and 2 per arm | each >= 0.85 |
| - | the labelling panel | >= 0.98 right on gold items, Fleiss kappa >= 0.80, at most 10% unsure |

Rows 4 to 7 are gold: true by construction. Natural items carry silver labels from a labelling panel
that works differently from the judge: three read-only sessions in the case's fixture, given its diff,
each lists every finding and names the one about the reference before answering; a split goes to an
adjudicator. No human label gates; the stamp records `human_audited = 0` until the maintainer audits a
sample of held-out labels and edits that count.

1. Add the `[[judge]]` and a reference on every case that asks it. Freeze the references: editing a
   held-out case's reference after the judge has run on it is tuning.
2. `python3 scripts/eval.py judge-probe <suite> --judge <id>`: 5 judge and 2 labeller calls on stored
   samples, printed raw. Check that the answer parses, the response names the judge's model, and the cost.
3. `python3 scripts/eval.py judge-label <suite> --judge <id>`: the panel labels every stored artifact the
   judge reads that has no label yet, into `judges/<id>/labels/<case>.toml`. It reads the samples `make
   eval-run` draws on arms `old` and `none` (`--arms`, `--base`), found by each case's key as it is now,
   so a sample drawn on an older fixture, runner or Claude Code is never labelled. A label once written
   is never changed. It prints each set's count per class: until each reaches 40, draw more sessions
   (`make eval-run ... SAMPLES=` above the count drawn) and label again. `--gold` then runs the panel on
   the gold items, one item at a time: hours for a few hundred items. If it is below 0.98 right, or the
   printed Fleiss kappa is below 0.80, the question or a reference is underspecified: stop and report it
   to the maintainer. `--labeller-model` picks the panel's model (Opus 5.5 by default).
4. Tune on dev: `python3 scripts/eval.py judge-align <suite> --judge <id> --set dev` prints each row and
   each disagreement. Read them, revise the question (or the prompt texts in `scripts/evals/jury.py`),
   repeat.
5. Freeze the version and run `--set held-out` once. It writes `judges/<id>/stamp.toml` with every
   row's counts once every item has its judge panel and every gold item its labelling panel, and
   otherwise prints INCOMPLETE and writes nothing. A version that misses the bar moves its held-out
   natural items to dev: draw and label fresh held-out sessions and try again, at most 3 versions
   per question; then report the missed bar.
6. Commit the labels and the stamp. The lint fails a stamp whose judge, labels or a stamped case's
   reference changed since it was written. After new labels or a dev case's reference edit, `--set
   held-out` stamps a cleared version again without counting a new version; it burns the held-out
   natural items like a missed version if it misses. A held-out case's edited reference must be
   restored. Never move a case out of `held_out` by hand: the stamp does not record the list, so it
   stays current, and that case's reference could then be edited and stamped again. A missed version
   moves its items to dev itself.

## Running and deciding

Every screen follows these steps; `make eval-plan TIER=<n>` prints the screens a tier takes. A scratch
suite is not screened: run and read it as "Smoke tests" says.

Screen and confirm once the change's text has settled: on a branch going through review rounds, on
the head its last round leaves, the closing round on its words included. A review fix that changes
text a session reads voids every earlier screen of it, so screening between rounds spends the runs
for nothing; between rounds, `make check` is enough.

1. **Fix the test before the first run.** The plan holds every file of the suite (cases, keys, baselines,
   references), the samples per case, the model ID, the Claude Code version, the runner's flags,
   `old`'s plugins (`new` changes as you iterate) and each judge's version. Your branch's first screen
   of a split on a model fixes it, each model keeping its own; a later screen with a different plan runs
   nothing and says what changed. `NEW_PLAN=1` (`--new-plan`) fixes a new one, and the PR says why.
   Never add samples after seeing a result.
2. **Check the suite can see the effect.** `make eval-size`, and `make eval-plan TIER=<n>` for the
   splits it reports, simulate the verdict rule at each split's size: the smallest harm it would catch
   80% of the time, under a `better` rule the smallest gain (both assuming independent units at a 0.5
   pass rate, the noisiest case), and per model the chance a positive control comes out WORSE, from the
   recorded baselines, with the samples per case that would reach 80%. The chance runs high. It reads
   each case's few baseline runs as its exact failure rate, so a case that failed 3 of 3 counts as one
   that always fails, and the baselines count each case's own checks, guards aside, so a target case
   whose checks the pass rule does not read adds to it though the verdict cannot see that case. Trust it
   only as far as the calibration's positive controls bear it out. A new skill has no positive control
   until it is on main, since removing it from `old` changes nothing. A split below 80% is too weak, and
   so is one missing `old` or `none` baselines on a gate model. At tier 4, for a direct suite, add cases
   the text changes on that model to a split below 80%, and record any missing baselines
   (`make eval-run ... RECORD=1`). Do not shrink the suite or the samples to save cost.
3. **Both arms run in the same screen,** interleaved, because the model changes over time and an older
   baseline mixes that in; which arm of a pair starts first alternates. Screen on the models
   `make eval-plan TIER=<n>` prints, one at a time (`MODEL=...`). Each arm draws the suite's
   `min_samples` per case unless `SAMPLES=` says otherwise.
4. **Rerun rather than reuse** when anything a session sees changes: the fixture, the runner's setup
   (bump `RUNNER` in `scripts/evals/session.py`, after which the lint demands fresh baselines; for the
   `gh` stub or the remote setup, `REMOTE_RUNNER` beside it, which redraws remote cases only and makes
   the lint demand fresh baselines of those, recorded with their `remote_runner`), the model
   or Claude Code. A screen reuses drawn samples only to resume or to regrade after a fix to a key;
   `make eval-run` keeps a case's samples per arm, model and Claude Code version, so a rerun regrades
   them and a larger `SAMPLES=` draws only the extra ones. Run `make check` on an edited case before
   drawing on it: a lint fix after the draw changes what the sessions saw.
5. **Count every sample.** A sample that fails for a reason outside the agent (an API error, a usage
   limit, a leak of user settings into the session, the session reaching the suite's files) is excluded
   and retried up to three times; when the API is limiting requests, each retry waits first, and once
   limits persist the run stops starting sessions and reports the rest as not run, so rerun it later to
   resume. While any sample is still excluded, the screen cannot SHIP, though harm it already shows
   still comes out HURT; its summary counts excluded and spoiled samples per arm. A sample the agent
   itself spoiled (a timeout, the budget or turn cap) counts as failing every check. A session times
   out after 30 minutes; a suite whose sessions run longer sets `timeout_s` in `suite.toml`, and
   changing it draws new samples.
6. **The verdict compares the arms task by task:** `new`'s mean minus `old`'s, per unit.
   - Under a `better` rule the primary metric is BETTER when an exact one-sided paired permutation test
     in that direction is below 0.05; under `no-regression` it is tested like a guard and never BETTER.
   - Any metric the pass rule reads is WORSE when the test for harm is below 0.05 divided among those
     metrics (Bonferroni), so a change that does nothing comes out HURT on a relative test by chance in
     at most 5% of screens. A must-hold failure is absolute, outside that bound.
   - A guard (each regression, cost or delivery metric) passes when the harm it shows is within its
     margin: the same test, run on each unit's difference plus the margin, is below 0.05. A guard, and
     a primary under `no-regression`, needs a `margin` above 0 in `suite.toml`, or it could never pass.
   - A reported metric is tested for harm the same way; one that comes out WORSE leaves the result as it
     is, and the PR explains it.
   - Anything else is INCONCLUSIVE, never "no change".
   - Gains and regressions are counted per unit and reported separately, with tokens, cost, turns and
     tool calls per arm.
7. **A rule that must hold every time,** such as keeping exploit detail out of public text, has an
   absolute bar: any failing sample under `new` is HURT, whatever `old` did. A clean result is not proof:
   no failure in n samples only puts the failure rate below about 3/n.
8. **The result:** SHIP when every guard passes and the primary is BETTER under a `better` rule, or passes
   too under `no-regression`; HURT when a metric the rule reads, or a must-hold one, is WORSE;
   INCONCLUSIVE otherwise. On a watch model a must-hold failure is printed as STANDING and left out of
   the result.
9. **Read transcripts before trusting a result:** every failing sample of the primary metric, of a
   must-hold metric and of any metric that came out WORSE (the screen lists each with its key), every
   sample whose judge panel split on the primary metric (listed too), every unit counted as a gain, two
   passing samples per arm picked at random, and any unit every arm fails, which is often a broken case.
   Look too for behaviour no check covers, such as a test skipped or a rule recited instead of followed.
   On `screen` and `confirm`, someone other than the author reads them and reports only whether the case
   is broken. A broken held-out case voids that run: fix it in `dev`, burn it, and rerun on fresh cases.
   A calibration screen chooses no text, so a case fixed during calibration stays on its split.
10. **Report a missed bar as it is,** with its baseline. Never set a new bar from the failing run.

## Commands

- `make eval-plan [TIER=<n>]`: the suites your change reaches, each marked DIRECT or INDIRECT, and the
  files no suite covers; with `TIER=<n>`, the steps that tier takes: the screens to run and what each
  direct suite's screened splits can see. Free.
- `make eval-size SUITE=<path>`: what each split can see on each model, from the recorded baselines.
  Free.
- `make eval-run SUITE=<path> ARM=none` (or `ARM=old`): run the cases on one arm, print each sample's key
  (for `show`), then how often each case failed its own checks, guards aside; `RECORD=1` writes the
  counts into the keys (one such run at a time: two at once can each drop the other's entry), `MODEL=`
  picks the model, `JUDGE=1` calls the judges (see Judges). `ARM=new` needs a `SPLIT`, since new
  results on held-out cases burn them.
- `make eval-screen SUITE=<path>`: run `old` and `new` on the `screen` split and print the result.
  `SPLIT=confirm` runs the confirm split, `NEW_PLAN=1` fixes a new plan, `JUDGE=1` calls the judges.
  The result and the samples to read are also written to `evidence/` in the store.
- The store holds every sample, plan and evidence file, and the judges' and labellers' answers:
  `grimoire-evals/` in the clone's git directory
  (`.git/grimoire-evals/` in the main checkout), shared by every worktree and never committed.
  `GRIMOIRE_EVALS_STORE=<dir>` puts it elsewhere. It used to be `~/.cache/grimoire-evals/`: copy that
  directory's contents in once, without overwriting what the new store already holds:

  ```bash
  cp -an ~/.cache/grimoire-evals/. \
    "$(git rev-parse --path-format=absolute --git-common-dir)/grimoire-evals/"
  ```

  Baseline (`run`) samples carry over. A screen begun before the store's default moved here, its samples
  copied or not, draws its samples again and needs `--new-plan` (`NEW_PLAN=1`) once: its plan named each
  arm's plugins by their path in the store.
- `python3 scripts/eval.py show <key>`: one sample's commits, final reply, the files its checks read,
  every `gh` call the stub logged (Claude Code's own included) and the `gh` text its checks read, skill
  deliveries and writes with the agent and spawn that made each, subagents' briefs and reports, and hook context.
- `python3 scripts/eval.py lint`: the mechanical checks from "Writing a case", and that each judge's
  stamp is current; `make verify` runs it.
- `python3 scripts/eval.py judge-probe`, `judge-label` and `judge-align`: calibrate a judge (see
  "Calibrating a judge"). Each takes the suite and `--judge <id>`, and spends inference.

## Calibrating the runner

After changing the runner or the verdict rule:

- Run at least 5 A/A screens, `old` against `old`: `python3 scripts/eval.py screen <suite>
  --new-ref <merge base> --new-plan --trial aa-1,aa-2,aa-3,aa-4,aa-5`. The trials share one pool of
  sessions, `--jobs` at a time (12 by default). The bar counts relative calls only: two or more screens
  with a metric BETTER or WORSE means the noise is underestimated. A must-hold failure in an A/A screen
  is not a false call but a limit of the text on that model, and a model whose A/A screens cannot SHIP
  is a watch model. Five screens catch only gross miscalibration: with a handful of tests each, they
  cannot tell a 5% false-call rate from 15%.
- Run one positive control: a copy of the text with one rule deleted, screened as `new`, on a split with
  enough cases of that rule; or, where no rule has that many, `--new-ref none`, which removes the whole
  target. It must come out WORSE on an outcome metric, not only on delivery.
- Calibrate on each model the suite lists.
- What it costs, as information for the PR: at calibration a session of the first suite cost about
  $0.18 on Opus 5.5, $0.11 on Sonnet 5.5 and $0.01 on Haiku 5.5, so one screen of its screen split at 3
  samples cost about $24, $14 and $1.

## What the runner does not cover

- Sessions load only this repository's plugins, with no user skills or settings, so a case cannot show how
  a skill competes with others a user has installed.
- Each session is one `claude -p` call: a case cannot test behaviour that should stop and ask the user,
  nor a workflow that spans sessions, such as a PR reviewed in one and its review addressed in the next.
- GitHub is a stub: `gh` answers only from the case's replies, the same for every call that matches, so
  a case shows what the agent sent, not what GitHub would do with it.
- The session's environment controls (GH_TOKEN, GH_CONFIG_DIR, GIT_ALLOW_PROTOCOL) hold only while it
  keeps the environment it is given: one that unsets GH_TOKEN and GH_CONFIG_DIR and runs the real `gh`
  by its path reaches the user's own `gh` login, and one that unsets GIT_ALLOW_PROTOCOL can reach the
  network with a key under HOME, since HOME stays the user's, which Claude Code needs.
- Sessions drawn in parallel share `/tmp`: a body or message file an agent writes at a fixed path
  there, such as `/tmp/pr-body.md`, can be overwritten by another session drawn at the same time, so a
  sample can record the other session's text.
- `origin` is a local path, not a github.com URL, and `git remote -v` prints that path: an agent that
  reads the owner or repository name from it finds none. When `build.py` names origin by a GitHub URL
  rewritten with `url.<path>.insteadOf`, `git remote -v` prints the rewritten local path, but
  `git config remote.origin.url` still gives the URL `build.py` set.
- The lint knows when a baseline predates the runner, not when the model or Claude Code changed; rerun
  baselines after either.
- A SendMessage follow-up to a subagent is not followed: `brief:<agent>` holds the prompts of the main
  thread's Agent calls that started that agent, and no follow-up. A delivery check with an `agent`
  reads every spawn of that agent, at any depth, as one; the spawn checks (Graders) tell them apart.
  The skills an agent's frontmatter preloads are read from a line of Claude Code's debug log, which it
  does not promise to keep: if that line changes, every preload reads as absent.
- A sample's venv uses the base Python's packages, the interpreter uv builds venvs on, not this
  checkout's `.venv`: that Python needs pytest, which the runner checks before the first session. The
  venv has no pip of its own, so a session's bare `pip install` reaches the base Python, where later
  samples see it; `python3 -m pip` stays in the sample.
- Claude Code's own context reaches every session, the account's name and email included: some
  sessions commit with that identity.
- A key fix regrades drawn samples once the screen is rerun with `NEW_PLAN=1` (the plan pins every file
  of the suite), except a fix that makes a check read a file or glob the samples did not collect, or a
  `verify` command they did not run: grading refuses, and the screen needs fresh samples (a new
  `--trial`).
- The check that a session stayed out of the suite reads the absolute paths in its tool calls, and the
  stub's `gh-stub-replies.json` by name: a relative path gets past it, such as `cd` into an arm then
  `ls ../../samples`, or `cat ../gh-stub/*` from the repository, and so does a path built from an
  environment variable that holds the store's path, such as `ls $GIT_CEILING_DIRECTORIES/samples`, and
  an absolute path that names a directory above one the check guards, such as `grep -r` over the
  sandbox or `/tmp`, which reaches the stub's `gh-stub/`.
- A run reads each case from the checkout as it was when the run began. A sample whose case changed on
  disk since (a branch switch, an edit) is excluded and retried, so keep the checkout still while a run
  draws.
