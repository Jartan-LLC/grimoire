# meterkit

meterkit reads electricity meter registers and turns them into usage intervals, bills and anomaly reports. Python 3.11 or later, standard library only; the package lives in `src/meterkit/`.

`tests/test_acceptance.py` holds the acceptance tests. Each module also gets tests of its own.

## Readings: `meterkit.readings`

The input is CSV with the header `meter,time,register`: a meter id, a local time written `YYYY-MM-DDTHH:MM`, and the meter's cumulative register in kWh, a decimal number with up to three decimals.

- `Reading(meter: str, time: datetime, register: Decimal)`: a frozen dataclass.
- `ReadingError(ValueError)`: raised for bad input.
- `parse_readings(text: str) -> list[Reading]`: the rows in file order; blank lines are skipped. A row with the wrong number of fields, a time or register that does not parse, or a negative register raises `ReadingError` with a message that starts with `line N:` and a space, counting the header as line 1.
- `Interval(meter: str, start: datetime, end: datetime, kwh: Decimal)`: a frozen dataclass.
- `intervals(readings: list[Reading]) -> list[Interval]`: for each meter, its readings sorted by time and each consecutive pair made an interval, `kwh` being the later register minus the earlier. The register counts up to 99999.999 and then starts again from 0, so when the later register is below the earlier one, `kwh` is the later register plus 100000 minus the earlier. The result is sorted by meter, then start. Two readings of one meter at the same time raise `ReadingError` naming the meter.

## Tariff: `meterkit.tariff`

- `Tariff(peak: Decimal, offpeak: Decimal, standing: Decimal)`: the price per kWh at peak and off-peak, and the standing charge per day.
- An interval is charged whole at the rate of the hour it starts in: peak from 07:00 to 22:59, off-peak otherwise.
- `Bill(peak_kwh: Decimal, offpeak_kwh: Decimal, days: int, total: Decimal)`: a frozen dataclass.
- `bill(intervals: list[Interval], tariff: Tariff) -> Bill`: `days` counts the distinct dates the intervals start on; `total` is the energy charge plus `days` times the standing charge, rounded to cents. Whether that rounding goes half up or half to even has not been settled yet.

## Anomalies: `meterkit.anomaly`

- `Anomaly(interval: Interval, median: Decimal)`: a frozen dataclass.
- `anomalies(intervals: list[Interval], factor: Decimal = Decimal(3)) -> list[Anomaly]`: for each meter, every interval whose `kwh` is more than `factor` times the median `kwh` of that meter's intervals (for an even count, the mean of the two middle values), with that median. A meter with fewer than three intervals has none. The result keeps the order of `intervals`.

## Command: `meterkit.cli`

`main(argv: list[str] | None = None) -> int` runs the `meterkit` command and returns its exit status.

- `meterkit usage FILE`: one line per interval, `meter start end kwh` separated by single spaces, times written `YYYY-MM-DDTHH:MM` and `kwh` with three decimals.
- `meterkit bill FILE --peak P --offpeak O --standing S [--meter M]`: bills every interval, or only meter M's, and prints four lines: `peak_kwh: <three decimals>`, `offpeak_kwh: <three decimals>`, `days: <n>` and `total: <two decimals>`.
- `meterkit anomalies FILE [--factor F]`: one line per anomaly, `meter start kwh median`, `kwh` and `median` with three decimals; nothing when there are none.

The exit status is 0 on success. An unreadable file or a `ReadingError` prints `meterkit: <message>` to stderr and exits 2.
