# rotakit

rotakit keeps a team's weekly on-call rota: planning the weeks, swapping them and exporting them to a calendar. Python 3.11 or later, standard library only. The package lives in `src/rotakit/`, where `model.py` holds the data model.

`tests/test_acceptance.py` holds the acceptance tests. Each module also gets tests of its own.

## Data model: `rotakit.model`

- `Person(id: str, name: str, away: tuple[date, ...] = ())`: `away` holds the Mondays of the weeks the person cannot take.
- `Week(start: date, person: str)`: a week on call, from Monday `start`, held by the person with id `person`.
- `Rota(people: list[Person], weeks: list[Week])`, kept as JSON by `load(path)` and `save(rota, path)`.
- `RotaError(Exception)`: a rota change that cannot be made.

## Planning: `rotakit.schedule`

- `plan(people: list[Person], first: date, count: int) -> list[Week]`: `count` weeks, the first starting on `first`. Each week goes to the next person in turn, in the order of `people`, who is not away that week; the turn then moves to the person after the one who took it. Raises `RotaError` when `first` is not a Monday, or when everyone is away in a week, naming that week's date.

## Swaps: `rotakit.swaps`

- `swap(rota: Rota, first: date, second: date) -> Rota`: a new rota with the people of the two weeks exchanged. Raises `RotaError` when either week is not in the rota, or when either person is away in the week they would take.
- `give(rota: Rota, week: date, person: str) -> Rota`: a new rota with that week handed to `person`. Raises `RotaError` when the week is not in the rota, the person is unknown, or the person is away that week.

## Calendar: `rotakit.ical`

- `to_ical(rota: Rota, person: str | None = None) -> str`: an iCalendar file of every week, or only `person`'s. The lines are `BEGIN:VCALENDAR`, `VERSION:2.0` and `PRODID:-//rotakit//EN`; then for each week in rota order `BEGIN:VEVENT`, `UID:<start as YYYYMMDD>-<person id>@rotakit`, `DTSTART;VALUE=DATE:<start as YYYYMMDD>`, `DTEND;VALUE=DATE:<the Monday after, as YYYYMMDD>`, `SUMMARY:On call: <name>` and `END:VEVENT`; then `END:VCALENDAR`. Every line ends with CRLF.

## Command: `rotakit.cli`

`main(argv: list[str] | None = None) -> int`. Every subcommand takes the rota file first.

- `rotakit plan ROTA --from YYYY-MM-DD --weeks N`: replaces the rota's weeks with N planned weeks, saves the rota and prints one line per week, `YYYY-MM-DD name`.
- `rotakit swap ROTA WEEK WEEK`: swaps the two weeks, given as `YYYY-MM-DD`, saves the rota and prints `swapped YYYY-MM-DD and YYYY-MM-DD`.
- `rotakit export ROTA [--person ID]`: prints the iCalendar file.

A `RotaError` prints `rotakit: <message>` to stderr and exits 1, leaving the rota file as it was.
