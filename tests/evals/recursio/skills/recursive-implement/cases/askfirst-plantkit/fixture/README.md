# plantkit

plantkit plans a vegetable garden: when to sow, how much to water and which plants should not share a bed. Python 3.11 or later, standard library only; the package lives in `src/plantkit/`. `examples/garden.toml` is a sample garden.

`tests/test_acceptance.py` holds the acceptance tests for the next release. Each module also gets tests of its own.

## Gardens and plants: `plantkit.model` (released)

- `Plant(name, family, sow_weeks: int, water_mm: float)`: a frozen dataclass; `CATALOG` maps each plant plantkit knows to its `Plant`. `water_mm` is the water it needs per week.
- `Garden(name, last_frost: date, first_frost: date, beds: dict[str, list[str]])`, read from a TOML file by `load_garden(path)`. Each bed lists plant names from `CATALOG`.
- `GardenError(Exception)`: a garden, rain file or request that cannot be used.

## Sowing: `plantkit.sowing` (released)

- `sow_dates(garden) -> list[tuple[date, str]]`: each plant in the garden once, with the date to sow it, `sow_weeks` weeks before the last frost; by date, then name.

## Rain: `plantkit.rain` (next release)

- `parse_rain(text: str) -> dict[date, float]`: CSV with the header `date,mm`, one rainfall in millimetres per row; blank lines are skipped and a date given twice adds up. A row with the wrong number of fields, a date that does not parse, or an amount that is not a number or is negative raises `GardenError` with a message that starts with `line N:` and a space, counting the header as line 1.

## Watering: `plantkit.watering` (next release)

- `weekly_water(garden, rain: dict[date, float], week: date) -> dict[str, float]`: for each bed, in the garden's order, the water its plants need that week, minus the rain from Monday `week` through the Sunday after, never below 0. Raises `GardenError` when `week` is not a Monday.

## Companions: `plantkit.companions` (next release)

- `BAD_PAIRS`: the families that should not share a bed: allium with legume, and nightshade with brassica.
- `conflicts(garden) -> list[tuple[str, str, str]]`: `(bed, plant, plant)` for each two plants in one bed whose families are a bad pair, the two plants in name order; sorted.

## Command: `plantkit.cli`

`main(argv: list[str] | None = None) -> int` runs the `plantkit` command.

- `plantkit sow GARDEN` (released): one line per plant, `YYYY-MM-DD plant`.
- `plantkit water GARDEN RAIN --week YYYY-MM-DD` (next release): one line per bed, `bed mm`, with one decimal.
- `plantkit check GARDEN` (next release): one line per conflict, `bed: plant + plant`; exits 1 when there are any.

Every subcommand prints to stdout, or writes to the file named by `--output FILE`. In the next release `--output` replaces `plantkit sow`'s `--out FILE` option, which goes away.

A `GardenError` or a file that cannot be read prints `plantkit: <message>` to stderr and exits 2.
