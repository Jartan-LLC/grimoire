# racekit

racekit turns a road race's chip times into results: each runner's time, their age category, and the places overall and within each category. It is plain JavaScript modules for Node 20 or later, with no dependencies: the source lives in `src/`, the tests in `test/`, and `node --test` runs them. Times are whole seconds.

`test/acceptance.test.js` holds the acceptance tests. Each module also gets tests of its own.

## Clock: `src/clock.js`

Already written: `RaceError`, the error for bad input; `parseClock(text)`, a `HH:MM:SS` time of day as seconds since midnight; and `formatDuration(seconds)`, a time as `H:MM:SS`, such as `0:41:07`.

## Results: `src/results.js`

The input is CSV with the header `bib,name,born,sex,start,finish`. `born` is a four-digit year, `sex` is `F` or `M`, and `start` and `finish` are the times of day the runner crossed the start and finish mats. A runner who did not finish has an empty `finish`.

- `parseResults(text)`: one `{ bib, name, born, sex, seconds }` per row, in file order, with `bib` and `born` as numbers and `seconds` the finish minus the start, or `null` without a finish. Blank lines are skipped. A row with the wrong number of fields, a bib that is not a whole number, a `born` that is not a four-digit year, a `sex` other than `F` or `M`, a time `parseClock` rejects, a finish that is not after its start, or a bib already used throws `RaceError` with a message that starts with `line N:` and a space, counting the header as line 1.
- `finishers(results)`: the runners with a time, fastest first, runners with the same time in file order.

## Categories: `src/categories.js`

- `ageOn(born, year)`: the runner's age on 31 December of the race's year.
- `category(born, sex, year)`: the sex, then the band: `U20` under 20, `SEN` from 20 to 34, and from 35 a `V` followed by the age rounded down to a multiple of 5, up to `V70` for 70 and over. So `FSEN`, `MV45`, `FU20`. An age under 10 throws `RaceError`.
- `compareCategories(a, b)`: sorts categories with every `F` category before every `M` one, and within a sex `U20`, `SEN`, then the `V` bands from youngest to oldest.

## Places: `src/places.js`

- `rank(finishers)`: each finisher with a `place`, counting from 1 in time order.
- Whether two finishers with the same time share a place has not been settled yet.
- `byCategory(finishers, year)`: a `Map` from each category that has finishers, in `compareCategories` order, to that category's finishers ranked as `rank` does, places counted within the category.

## Command: `src/cli.js`

`run(argv, readText)` runs the `racekit` command without touching the process, so tests can call it, and returns `{ status, output, error }`; `readText(path)` reads a file. `bin/racekit.js` wires it to the process.

- `racekit results FILE YEAR`: one line per finisher in place order, `place bib name time category`, separated by single spaces, the time by `formatDuration`; then `DNF bib name` for each runner without a finish, in file order.
- `racekit results FILE YEAR --category CAT`: only that category's finishers, with their places in the category, and no DNF lines.
- `racekit winners FILE YEAR`: for each category with finishers, in category order, `category bib name time` for its first place.

The status is 0 on success. A file that cannot be read, a `RaceError` or a bad command line sets status 2 and the error `racekit: <message>` with a newline.
