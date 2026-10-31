# hivekit

hivekit keeps a beekeeping club's hive inspection log and says which hives need attention and how much honey they hold. Python 3.11 or later, standard library only; the package lives in `src/hivekit/`.

`tests/test_acceptance.py` holds the acceptance tests. Each module also gets tests of its own.

## Inspection log: `hivekit.log`

The log is CSV with the header `hive,date,brood,honey,queen,temper`: the hive's id, the date as `YYYY-MM-DD`, the frames of brood and of honey (whole numbers from 0 to 10), `yes` or `no` for whether the queen or her eggs were seen, and the colony's temper from 1 (calm) to 5 (fierce).

- `Inspection(hive: str, date: date, brood: int, honey: int, queen: bool, temper: int)`: a frozen dataclass.
- `LogError(ValueError)`: a log that cannot be read.
- `parse_log(text: str) -> list[Inspection]`: every row, sorted by hive, then date; blank lines are skipped. A row with the wrong number of fields, a date that does not parse, a number out of its range or a `queen` other than `yes` or `no` raises `LogError` with a message that starts with `line N:` and a space, counting the header as line 1. Two rows for one hive on one date raise `LogError` naming the hive.
- `by_hive(log: list[Inspection]) -> dict[str, list[Inspection]]`: each hive's inspections in date order, hives sorted.

## Health: `hivekit.health`

- `flags(history: list[Inspection]) -> list[str]`: for one hive's inspections in date order, judged on the latest, in this order: `queenless` when the queen was seen in neither of the last two inspections, `crowded` when brood and honey frames add up to 9 or more, and `defensive` when the temper is 4 or more. A hive with one inspection is never `queenless`.
- `overdue(log: list[Inspection], today: date, days: int = 10) -> list[str]`: the hives whose latest inspection is more than `days` days before `today`, sorted.

## Honey: `hivekit.honey`

- `FRAME_KG`: the kilograms of honey one full frame holds. The figure has not been settled yet: 2.0 suits the national frames most members use, 2.5 the deeper frames some have.
- `honey_kg(inspection) -> float`: the honey frames times `FRAME_KG`.
- `gains(history: list[Inspection]) -> list[tuple[date, float]]`: for each inspection after the first, its date and the change in `honey_kg` since the one before.

## Command: `hivekit.cli`

`main(argv: list[str] | None = None) -> int` runs the `hivekit` command; every subcommand takes the log file first.

- `hivekit status LOG --today YYYY-MM-DD`: one line per hive, sorted: the hive, the date of its latest inspection, then its flags joined with commas, or `ok` when it has none, then a space and `(overdue)` when it is overdue.
- `hivekit honey LOG`: one line per hive, sorted: the hive and the honey of its latest inspection in kilograms, with one decimal.

The exit status is 0 on success. A file that cannot be read or a `LogError` prints `hivekit: <message>` to stderr and exits 2.
