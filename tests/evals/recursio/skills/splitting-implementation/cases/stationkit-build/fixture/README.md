# stationkit

Reads the files our weather-station loggers write, checks the readings, and summarises them by
day, as a library and a command.

## Data model

`src/stationkit/model.py` holds the records the modules pass to one another: `Reading` (one
observation in SI units, UTC time), `Flag` and `FlagKind` (a quality-control finding), and
`DailySummary` (one station's day). Every module below works on these and nothing else of its
siblings, except the command, which uses them all.

## Ingest (`stationkit.ingest`)

Three readers, each taking the file's lines and returning an `IngestResult`: the `Reading`s in file
order and a list of `LineError(line, message)`, numbered from 1. A bad line is reported and skipped;
reading goes on. Every reader converts to the model's units: C, %, hPa, m/s and mm.

- `read_logger_csv(lines, station, tz)`: the console logger's CSV export. A header row names the
  columns, matched by name in any order, extra columns ignored: `Date` (`mm/dd/yy`), `Time`
  (`h:mma`, as `1:30a` or `12:05p`), `Temp Out` (F), `Out Hum` (%), `Bar` (inHg), `Wind Speed`
  (mph), `Hi Speed` (mph) and `Rain` (inches). `---` is a missing value. Times are local in the
  IANA zone `tz`: a time that does not exist (the spring-forward hour) is a line error, and in the
  fall-back hour a time earlier than the previous row's is the second occurrence.
- `read_fixed_width(lines)`: the hourly archive, one record per line, columns counted from 1.
  Lines starting with `#` are comments; a record shorter than 48 characters is a line error.

  | Columns | Field | Unit | Missing |
  |---------|-------|------|---------|
  | 1-6 | station id, space-padded | | |
  | 8-19 | time, `YYYYMMDDHHMM` | UTC | |
  | 21-25 | air temperature, signed | tenths of C | `99999` |
  | 27-29 | relative humidity | % | `999` |
  | 31-35 | station pressure | tenths of hPa | `99999` |
  | 37-39 | wind speed | knots | `999` |
  | 41-43 | gust | knots | `999` |
  | 45-48 | rain since the previous record | tenths of mm | `9999` |

- `read_ndjson(lines, station)`: the field sensors' JSON lines, one object per line: `ts` (ISO 8601
  with an offset or `Z`), `t` (C), `rh` (%), `p` (hPa), `ws` and `wg` (m/s), `r` (mm). A missing or
  null key is a missing value; unknown keys are ignored. A line that is not an object, or whose `ts`
  is missing or has no offset, is a line error. Blank lines are skipped.

`read_file(path, station, tz)` picks the reader by extension: `.csv`, `.dat`, `.ndjson` or `.jsonl`.

## Quality control (`stationkit.qc`)

`check(readings, limits=DEFAULT_LIMITS)` returns the `Flag`s for a list of readings that may mix
stations and come in any order, sorted by station, then time, then kind. Each station is checked
on its own readings in time order.

- **Range**: a value outside its limits. Defaults: temperature -60 to 60 C, humidity 0 to 100 %,
  pressure 870 to 1085 hPa, wind 0 to 75 m/s, gust 0 to 100 m/s, rain 0 to 50 mm per reading. A gust
  below the same reading's wind speed is a range flag on the gust.
- **Step**: a change from the previous in-range value larger than the allowance: 3 C of
  temperature, 20 points of humidity or 2 hPa of pressure per 10 minutes, scaled by the time
  between the two readings and never less than the 10-minute allowance. The later reading is
  flagged.
- **Flatline**: temperature, humidity, pressure or wind holding exactly the same value on 12 or
  more consecutive readings spanning at least 2 hours. Every reading of the run is flagged. Wind at
  0 is calm, not stuck; rain is never flatline-checked.
- **Gap**: two consecutive readings further apart than 3 times the station's median interval. The
  reading after the gap gets a flag with no field, and its detail gives the gap's length.

## Derived values and daily summaries (`stationkit.derive`)

- `dew_point_c(temperature_c, humidity_pct)`: the Magnus formula with a = 17.62 and b = 243.12 C;
  None at 0 % humidity.
- `heat_index_c(temperature_c, humidity_pct)`: the US National Weather Service algorithm, worked in
  Fahrenheit: Steadman's simple formula, switching to the Rothfusz regression with its low-humidity
  and high-humidity adjustments when the average of the simple result and the temperature is 80 F or
  more.
- `wind_chill_c(temperature_c, wind_ms)`: the 2001 North American wind-chill index,
  13.12 + 0.6215 T - 11.37 V^0.16 + 0.3965 T V^0.16 with V in km/h; None above 10 C or below
  4.8 km/h.
- `daily(readings, flags, tz, day_start_hour=0)`: one `DailySummary` per station and local day in
  the IANA zone `tz`, sorted by station and day. With `day_start_hour=9`, a day runs from 09:00 to
  09:00 the next morning and takes the date it starts on. A value with a flag on its field is left
  out; a gap flag leaves the reading in. Coverage is the day's readings against the readings the
  station's median interval would give, capped at 100 %; a day is complete at 80 % or more.
  Temperature min, max and mean, the highest gust, the rain total and the mean pressure come from
  the values left; a field with none is None.
- `degree_days(summaries, base_c=18.0)`: heating and cooling degree days per station, from each
  day's (min + max) / 2, skipping days missing either.

## Reports (`stationkit.report`)

Each renderer takes a list of `DailySummary` and returns a string.

- `render_text`: one table per station under its id, columns Day, Min, Max, Mean, Gust, Rain,
  Pressure and Coverage, right-aligned, one decimal place, `-` for a missing value. An incomplete
  day has `*` after its date, and the table ends with the footnote `* under 80% coverage`.
- `render_csv`: a header row of the `DailySummary` field names in order, then one row per summary:
  ISO dates, an empty cell for a missing value, `true`/`false` for `complete`, quoted as RFC 4180
  requires.
- `render_markdown`: per station and calendar month, a table of the days, then a summary line: the
  mean of the daily means, the highest maximum and the lowest minimum with their dates, the rain
  total and the rain days (0.2 mm or more).

## Command (`stationkit.cli`)

- `stationkit summary [--format text|csv|markdown] [--tz ZONE] [--climate-day] [--station ID] FILE...`
  reads each file, runs the quality checks, and prints the daily report of every file's readings
  together. `--tz` defaults to UTC, `--climate-day` starts days at 09:00, and `--station` names the
  station for formats that do not carry one, defaulting to the file's stem. For each file it prints
  `FILE: N readings, M flagged` to stderr.
- `stationkit qc [--tz ZONE] [--station ID] FILE...` prints one line per flag:
  `station time kind field detail`, with `-` for no field.

Line errors print to stderr as `FILE:LINE: message`. The exit status is 0, or 1 when any file had
line errors, or 2 when a file cannot be read or has an extension no reader takes; the other files
are still processed.

## Status

Only the data model exists.
