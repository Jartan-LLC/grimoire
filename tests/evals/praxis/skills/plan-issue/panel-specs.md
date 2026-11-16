# Grading specs: plan-issue panel cases

The blind panel's questions for plan-issue's abstraction and clash cases. Three agents grade
each plan, seeing neither the arm nor the model, and answer its case's one question yes or
no; two of three decide. The panel is the bar for a change to plan-issue or to the
`praxis:planning` skill (the suite's `[pass_rule]` comment says how). The refused-input
question is a reference for one case's check, not part of the bar.

Each grader gets, per case, the prompt (prompt.md), the issue the gh stub serves (its title
and body, from the key's `[[gh]]` reply), the path of the fixture the planner saw, and the
question below for the case's kind. A grader may read the fixture and `build.py` to check a
claim, never the case's `key.toml` or `reference/`, which hold the expected answer.

The questions are the ones plan-issue's blind panel for the planning skill (#193) used on Opus plans of
six cases: cart-price-format, thumb-retry, frost-sms-alert, liftlog-markdown,
notes-sync-clash and report-output-flag. Every other case takes the question of its kind
unchanged, chosen from the case's kind alone, without seeing any plan for it.

Case paths below are relative to `tests/evals/praxis/skills/plan-issue/cases/`.

## Questions

### Second caller

A second caller of the logic the issue needs already exists in the fixture.

> Does the plan have the new code and the existing code share one implementation of the
> logic they both need (calling, moving or extracting the existing code), rather than
> copying it or writing a second version? Answer yes if it shares, no if it copies,
> reimplements, or only offers sharing as an option it does not take.

A yes passes.

### One use

An abstraction is tempting, but the change has one use.

> Does the plan add an abstraction that only uses which do not exist yet would need: an
> interface, base class, registry, plugin or provider layer, a generic
> notifier/formatter/exporter, or an option or parameter no caller in this change uses? A
> parameter added so tests can inject a clock, path or stub does not count. Answer yes if it
> adds one, no if it builds only what this one use needs.

A no passes.

### Clash

The requested command or flag name already means something else in the fixture.

> The requested name already has a meaning in this project (see the fixture). Does the plan
> say that the name already means something else here and leave the choice (reuse, rename,
> change the old meaning) to the user, as a question or a decision with a default? Answer
> yes if it does, no if it silently overrides the existing meaning, silently picks another
> name, or does not notice.

A yes passes.

### Refused input

Only colcut-fields-errors takes it. It is not part of the `[pass_rule]` bar: it says which plans
the case's refused-input check must pass, written blind from the case's prompt, issue, fixture and
plan-format.md.

The issue adds `--fields LIST` to a CLI (`bin/colcut.js`) that today exits 2 with a usage line on
bad arguments, and a field list like `2,4-6` has values it must refuse.

> Does the plan's Verification section include at least one check that gives `--fields` a value the
> plan treats as invalid and states the expected refusal (a non-zero exit, an error message, or a
> thrown error)? Count a CLI command, a fenced shell block, a named unit test of the list parser, or
> a prose check, as long as it sits under Verification and names or clearly describes the refused
> input: for example `0` or a negative field, a non-number (`a`), an empty list or empty item
> (`2,,4`), a reversed range (`6-4`), or `--fields` with no value. An open range such as `4-` or
> `-3` counts only if the plan says it is refused. Do not count: a refusal described only under
> Approach, Steps or Decisions; a test named in passing without saying it feeds a refused value
> ("add tests for the parser", "`npm test` passes"); an error case not about the value of `--fields`
> (no file argument, a file that does not exist, an unknown option); a field past the end of a row,
> which prints an empty value and is not refused.

A yes passes.

## Cases

| Case | Question |
|---|---|
| authors-paging | Second caller |
| cart-price-format | Second caller |
| thumb-retry | Second caller |
| remind-duration-parse | Second caller |
| tag-page-slugs | Second caller |
| invoice-date-range | Second caller |
| signup-email-check | Second caller |
| backup-slack-alert | One use |
| frost-sms-alert | One use |
| liftlog-markdown | One use |
| loan-reminder-email | One use |
| relnotes-html | One use |
| sales-csv-export | One use |
| quiz-results-json | One use |
| upload-size-limit | One use |
| paste-rate-limit | One use |
| rates-cache | One use |
| notes-sync-clash | Clash |
| report-output-flag | Clash |
| timer-flag-clash | Clash |
| dotfiles-link-clash | Clash |
| jsonfmt-indent-flag | Clash |
| docs-check-clash | Clash |
| shelf-search-clash | Clash |
| colcut-fields-errors | Refused input (check reference, not the bar) |
