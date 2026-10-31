# gradekit

gradekit turns a course's raw scores into weighted percentages, letter grades and a class report. It is TypeScript that Node 24 or later runs directly, with no dependencies and no build step: the source lives in `src/`, the tests in `test/`, and `node --test` runs them. Relative imports name the `.ts` file.

`test/acceptance.test.ts` holds the acceptance tests. Each module also gets tests of its own.

## Scores: `src/scores.ts`

The input is CSV with the header `student,item,points,max`. An item is named `category:name`, such as `hw:1` or `exam:final`.

- `type Score = { student: string; item: string; points: number; max: number }`.
- `class ScoreError extends Error`: bad input, in scores or weights.
- `parseScores(text: string): Score[]`: the rows in file order; blank lines are skipped. A row with the wrong number of fields, a `points` or `max` that is not a number, a `max` that is not above 0, or `points` below 0 or above `max` throws `ScoreError` with a message that starts with `line N:` and a space, counting the header as line 1.

## Weights: `src/weights.ts`

- `type Weights = Record<string, number>`: each category's weight, in percent.
- `parseWeights(text: string): Weights`: one `category = weight` line per category; blank lines and lines starting with `#` are skipped. A line that does not parse throws `ScoreError` naming its line; weights that do not add up to 100 throw `ScoreError` with the sum in its message.
- `percentages(scores: Score[], weights: Weights): Map<string, number>`: each student's percentage, from 0 to 100 and not rounded, keyed by student in name order. A category scores the student's points over the maximum across all its items, times its weight; a category the student has no items in scores 0. An item whose category has no weight throws `ScoreError` naming the item.

## Letters and the curve: `src/letters.ts`

- `type Cutoffs = [letter: string, min: number][]`, highest first; `DEFAULT_CUTOFFS` is A 90, B 80, C 70, D 60, F 0.
- `letter(percent: number, cutoffs: Cutoffs = DEFAULT_CUTOFFS): string`: the first letter whose `min` the percentage reaches.
- Whether a percentage is rounded to a whole number before its letter is chosen, so that 89.5 earns an A, has not been settled yet.
- `distribution(letters: string[], cutoffs: Cutoffs = DEFAULT_CUTOFFS): Map<string, number>`: how many of each letter, every letter of `cutoffs` present in their order, zeros included.
- `curve(percents: Map<string, number>, target: number): Map<string, number>`: when the class mean is below `target`, every percentage is raised by the difference, none above 100; otherwise the percentages are returned unchanged. The keys keep their order.

## Command: `src/cli.ts`

`run(argv: string[], readText: (path: string) => string): { status: number; output: string; error: string }` runs the `gradekit` command without touching the process, so tests can call it; `bin/gradekit.ts` wires it to the process.

- `gradekit report SCORES WEIGHTS [--curve MEAN]`: one line per student in name order, `student percent letter`, separated by single spaces, the percentage with one decimal (`formatPercent` in `src/format.ts`). With `--curve`, the percentages are curved to the mean first.
- `gradekit dist SCORES WEIGHTS`: one line per letter in cutoff order, `letter count`.

The status is 0 on success. A file that cannot be read, a `ScoreError` or a bad command line sets status 2 and the error `gradekit: <message>` with a newline.
