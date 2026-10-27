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

Run `make eval-plan`. It lists the suites that cover your change and the changed files no suite covers.

- If it lists a suite, screen the change with it, then confirm it before opening the PR.
- If a changed file is uncovered and the edit targets a behaviour you have seen go wrong, write cases
  first, then edit. If you judge an uncovered change not worth a suite, say why in the PR description.
- Only text the model never reads needs no eval: a README, a changelog. A fix inside a skill, agent,
  command or hook file, even a link or a heading, reaches the model; screen it when a suite covers it.
  Such a screen can show only large breakage: the fix goes ahead when nothing comes out WORSE, and the PR
  says what the screen showed.

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
   `make eval-plan` says when a split has too few.
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
  each branch tracking it, so `git push` works, and `origin/HEAD` names `main`, as in a clone. To start
  with a branch ahead of, behind or missing from `origin`, `build.py` makes `origin` itself with
  `git init --bare -b <the fixture's default branch> ../origin.git`, pushes that branch, so `origin/HEAD`
  can name it, and pushes what else it wants there: the runner keeps an `origin` that `build.py` made as
  `build.py` left it, adding only `origin/HEAD` when the repository lacks it and origin's HEAD names a
  branch origin holds. That `origin` is a local path, or a URL `url.<path>.insteadOf` rewrites to one:
  git refuses any other. The session's `gh` is a stub that records every call and answers from the key's
  `[[gh]]` tables: the first whose `match` regex finds the call's arguments joined with spaces, each
  newline in them written as `\n` (`pr create --draft --title ...`), prints its `stdout` and exits with
  its `exit` (default 0). A call no reply matches fails with `gh stub: no reply for: <arguments>`, so
  script every call the task needs, reads (`gh pr view`, `gh api`) included. A `[[gh]]` table implies
  `remote = true`, and the replies count in the case hash, like the fixture.

  Write each `match` to accept every call the task could make at that step, anchored on the subcommand
  (`^pr create`), and grade the behaviour under test with a check, never with a `match`: a narrow match
  (`--draft`) fails the other calls, and the failure invites the agent to retry until it hits the
  scripted one. The session could read the answer too: the replies sit in its sandbox, so a sample
  whose tool calls name the stub's directory or `replies.json` is excluded.

  ```toml
  [[gh]]
  match = '^pr create'
  stdout = "https://github.com/acme/app/pull/7\n"
  ```

- **Keep tool configuration out of a fixture.** A fixture whose `pyproject.toml` has a `[tool.ruff]`
  table gets a `.ruff_cache/` written into it by the commit hooks, and the case hash counts every file in
  the fixture, so each hook run would redraw the case's samples.
- **Check the checks.** Write several passing references that differ in wording, order and approach, and
  failing references for the target check. The lint runs the checks on all of them. Prefer checks on what
  the agent produced over checks on how it got there.
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

- **Grade what the agent produced:** a regex over the commit messages, the final reply or a file. An
  `absent` check fails when the agent produced nothing to check.
- **Whether a skill was in context when the agent wrote** is a guard or a diagnostic, not a primary
  metric, except in trigger cases, where loading the skill is the behaviour under test.
- **A subagent's work:** `report:<agent>` is every report that agent handed back, `brief:<agent>` every
  Agent-call prompt the main thread sent that agent type (a call that ended in error aside), and a delivery check with
  `agent = "<plugin>:<agent>"` reads that subagent's skill loads and writes instead of the main
  thread's. A reference gives reports under `[reports]` and briefs under `[briefs]`, as
  `"<plugin>:<agent>" = "text"`.
- **What the agent sent to GitHub:** `gh` is every call the stub recorded, one `gh <arguments>` line each
  with newlines written as `\n`, then the text of each `--body` (and `-b` where it means `--body`),
  `gh release` `--notes` or `-n`, `gh pr` and `gh issue` `close` and `reopen` `--comment` or `-c`,
  `gh api` `body=` field, body file or stdin they passed. The calls Claude Code makes on its own
  (`gh pr view --json url` and `gh pr view <branch> --json url` on 2.1.311) are left out, so no check
  grades them. A reference gives it as `gh = "text"`. The lint fails a `gh` check on a case without a
  remote.
- **Judges are not built yet.** When a check cannot decide, a judge will answer one yes/no question about
  one output, with the reference answer, outputs stripped of skill and arm names, and "unknown" counted
  as a fail; and it will be calibrated first, against outputs the maintainer labelled.

## Running and deciding

1. **Fix the test before the first run.** The plan holds every file of the suite (cases, keys, baselines,
   references), the samples per case, the model ID, the Claude Code version, the runner's flags and
   `old`'s plugins (`new` changes as you iterate). Your branch's first screen of a split on a model fixes
   it, each model keeping its own; a later screen with a different plan runs nothing and says what
   changed. `NEW_PLAN=1` (`--new-plan`) fixes a new one, and the PR says why. Never add samples after
   seeing a result.
2. **Check the suite can see the effect.** `make eval-plan` and `make eval-size` simulate the verdict
   rule at each split's size: the smallest harm it would catch 80% of the time, under a `better` rule the
   smallest gain (both assuming independent units at a 0.5 pass rate, the noisiest case), and per model
   the chance a positive control comes out WORSE, from the recorded baselines, with the samples per case
   that would reach 80%. The chance runs high. It reads each case's few baseline runs as its exact
   failure rate, so a case that failed 3 of 3 counts as one that always fails, and the baselines count
   each case's own checks, guards aside, so a target case whose checks the pass rule does not read adds
   to it though the verdict cannot see that case. Trust it only as far as the calibration's positive
   controls bear it out. A new skill has no positive control until it is on main, since removing it from
   `old` changes nothing. A split below 80% is too weak: add cases the text changes on that model. So is
   one missing `old` or `none` baselines on a gate model: record them (`make eval-run ... RECORD=1`). Do
   not shrink the suite or the samples to save cost.
3. **Both arms run in the same screen,** interleaved, because the model changes over time and an older
   baseline mixes that in; which arm of a pair starts first alternates. Screen on every model the suite
   lists, one at a time (`MODEL=...`), as `make eval-plan` prints. Each arm draws the suite's
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
   itself spoiled (a timeout, the budget or turn cap) counts as failing every check.
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
   must-hold metric and of any metric that came out WORSE (the screen lists each with its key), every unit
   counted as a gain, two passing samples per arm picked at random, and any unit every arm fails, which is
   often a broken case. Look too for behaviour no check covers, such as a test skipped or a rule recited
   instead of followed. On `screen` and `confirm`, someone other than the author reads them and reports
   only whether the case is broken. A broken held-out case voids that run: fix it in `dev`, burn it, and
   rerun on fresh cases. A calibration screen chooses no text, so a case fixed during calibration stays
   on its split.
10. **Report a missed bar as it is,** with its baseline. Never set a new bar from the failing run.

## Commands

- `make eval-plan`: the suites your change needs, the files no suite covers, and what each split can see.
  Free.
- `make eval-size SUITE=<path>`: what each split can see on each model, from the recorded baselines.
  Free.
- `make eval-run SUITE=<path> ARM=none` (or `ARM=old`): run the cases on one arm and print how often each
  failed its own checks, guards aside; `RECORD=1` writes the counts into the keys (one such run at a
  time: two at once can each drop the other's entry), `MODEL=` picks the model. `ARM=new` needs a
  `SPLIT`, since new results on held-out cases burn them.
- `make eval-screen SUITE=<path>`: run `old` and `new` on the `screen` split and print the result.
  `SPLIT=confirm` runs the confirm split, `NEW_PLAN=1` fixes a new plan. The result and the samples to
  read are also written to `evidence/` in the store.
- The store holds every sample, plan and evidence file: `grimoire-evals/` in the clone's git directory
  (`.git/grimoire-evals/` in the main checkout), shared by every worktree and never committed.
  `GRIMOIRE_EVALS_STORE=<dir>` puts it elsewhere. It used to be `~/.cache/grimoire-evals/`: move that
  directory's contents in once. Baseline (`run`) samples carry over. A screen begun before the store's
  default moved here, its samples moved or not, draws its samples again and needs `--new-plan`
  (`NEW_PLAN=1`) once: its plan named each arm's plugins by their path in the store.
- `python3 scripts/eval.py show <key>`: one sample's commits, final reply, the files its checks read,
  `gh` calls, skill deliveries and writes with the agent that made each, subagents' briefs and reports,
  and hook context.
- `python3 scripts/eval.py lint`: the mechanical checks from "Writing a case"; `make verify` runs it.

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
- `origin` is a local path, not a github.com URL, and `git remote -v` prints that path, even when
  `build.py` names origin by a GitHub URL rewritten with `url.<path>.insteadOf`: an agent that reads
  the owner or repository name from the remote finds none.
- The lint knows when a baseline predates the runner, not when the model or Claude Code changed; rerun
  baselines after either.
- A subagent's own subagents are not followed, nor is an Agent call run in the background, nor a
  SendMessage follow-up: `brief:<agent>` holds only the prompts of the Agent calls that started it. A
  delivery check with an `agent` reads every spawn of that agent as one. The skills an agent's
  frontmatter preloads are read from a line of Claude Code's debug log, which it does not promise to
  keep: if that line changes, every preload reads as absent.
- A sample's venv uses the base Python's packages, the interpreter uv builds venvs on, not this
  checkout's `.venv`: that Python needs pytest, which the runner checks before the first session. The
  venv has no pip of its own, so a session's bare `pip install` reaches the base Python, where later
  samples see it; `python3 -m pip` stays in the sample.
- Claude Code's own context reaches every session, the account's name and email included: some
  sessions commit with that identity.
- A key fix regrades drawn samples once the screen is rerun with `NEW_PLAN=1` (the plan pins every file
  of the suite), except a fix that makes a check read a file the samples did not collect: grading
  refuses, and the screen needs fresh samples (a new `--trial`).
- The check that a session stayed out of the suite reads the absolute paths in its tool calls, and the
  stub's `replies.json` by name: a relative path gets past it, such as `cd` into an arm then
  `ls ../../samples`, or `cat ../gh-stub/*` from the repository.
- A run reads each case from the checkout as it was when the run began. A sample whose case changed on
  disk since (a branch switch, an edit) is excluded and retried, so keep the checkout still while a run
  draws.
