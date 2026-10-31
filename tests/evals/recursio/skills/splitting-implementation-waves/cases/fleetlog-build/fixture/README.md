# fleetlog

Keeps the records of a company's vehicle fleet -- fill-ups, servicing and the trip log -- and
answers the questions the fleet manager asks of them, as a library and a command.

## Data model

`src/fleetlog/model.py` holds the records the modules pass to one another: `Vehicle` and
`FuelKind`, `FillUp`, `ServiceRecord`, `Trip`, and `FleetError`. Every module below works on these
and nothing else of its siblings, except the command, which uses them all. Bad input raises
`FleetError` with a message naming the vehicle, record or value at fault. Money and litres are
`decimal.Decimal`, never floats; "rounded" means rounded half up.

## Fuel economy (`fleetlog.economy`)

- `segments(fillups)` takes one vehicle's fill-ups in any order and returns its `Segment`s
  (defined in this module: `start_km`, `end_km`, `litres`, `l_per_100km`), in odometer order. A
  segment runs from one full fill to the next full fill. Its litres are those of every fill after
  the first full one, up to and including the next full one, so partial fills in between count.
  Fills before the first full fill, and partial fills after the last one, are in no segment.
  `l_per_100km` is litres over distance x 100, rounded to 2 places. Two fills at the same
  odometer reading, or fill-ups of more than one vehicle, are an error.
- `average(fillups)`: the total litres of all segments over their total distance x 100, rounded
  to 2 places; None when there is no segment.
- `outliers(segments, tolerance=Decimal("0.3"))`: the segments whose `l_per_100km` is more than
  `tolerance` (a fraction) above or below the median of all of them, in their given order. The
  median of an even count is the mean of the middle two.
- `cost_per_km(fillups)`: the cost of the fills counted in segments over the segments' total
  distance, rounded to 3 places; None when there is no segment.

## Service schedule (`fleetlog.service`)

`SCHEDULE` lists, in this order: the oil change every 15,000 km or 12 months, whichever comes
first; tyre rotation every 10,000 km; brake fluid every 24 months; inspection every 24 months,
the first one 36 months after purchase. Electric vehicles have no oil change. The record kinds
are `oil`, `tyres`, `brakes` and `inspection`.

- `due(vehicle, records, today, odometer_km)` returns one `Due` (defined in this module: `kind`,
  `due_day`, `due_km`, `status`) per scheduled item for that vehicle. Each interval counts from
  the vehicle's latest record of that kind, by day; with no record, from the purchase date at
  0 km. A month step keeps the day of the month, moved back to the month's last day when the
  month is shorter (31 January plus one month is 28 or 29 February). `due_day` is None for an
  item counted in km only, `due_km` None for one counted in months only.
- `status` is `overdue` when `today` is on or after `due_day` or `odometer_km` is at or past
  `due_km`; `due-soon` when within 30 days of `due_day` or 1,000 km of `due_km`; otherwise `ok`.
  The list is ordered overdue, then due-soon, then ok, and in `SCHEDULE` order within each.
- Records of other vehicles are ignored. A record dated after `today` is an error.

## Trip log (`fleetlog.trips`)

- `check(trips)` returns a `Problem` (defined in this module: `trip`, the 0-based index in the
  input list; `kind`; `detail`) for each fault, ordered by `trip` and then by the kinds' order
  here:
  - `times`: the trip does not end after it starts.
  - `odometer`: `end_km` is below `start_km`.
  - `gap`: taking each vehicle's trips by start time, a trip whose `start_km` is not the previous
    trip's `end_km`. The detail is `gap of N km`, N being the start minus the previous end (it can
    be negative).
  - `overlap`: a trip that starts before the vehicle's previous trip ended.
  - `driver`: a trip that overlaps in time a trip of the same driver in another vehicle; only the
    one that starts later is flagged.
  - `speed`: an average speed above 150 km/h.
- `mileage(trips, year, month)` returns a dict of driver to the km of the trips that start in
  that month, with the drivers in sorted order.

## Running costs (`fleetlog.costs`)

- `value(vehicle, day)`: straight-line depreciation to 10 % of the price over 8 years (2,922
  days): `price - 0.9 x price x min(days since purchase / 2922, 1)`, rounded to cents. A day
  before purchase is an error.
- `running_costs(vehicle, fillups, services, start, end)` returns `Costs` (defined in this module:
  `fuel`, `service`, `depreciation`, `total`, `distance_km`, `per_km`) for the vehicle's records
  dated from `start` to `end` inclusive. `fuel` and `service` are the sums of their costs;
  `depreciation` is `value(start) - value(end)`; `total` is the three added. `distance_km` is the
  highest minus the lowest odometer reading among those fills and services, 0 with fewer than
  two; `per_km` is total over distance, rounded to 3 places, or None at 0 km. Records of other
  vehicles are ignored.

## Command (`fleetlog.cli`)

Files are CSV with a header row:

- vehicles: `reg,make,fuel,bought,price`
- fill-ups: `reg,day,odometer_km,litres,cost,full`, where `full` is `yes` or `no`
- services: `reg,day,odometer_km,kind,cost`
- trips: `reg,driver,start,end,start_km,end_km,purpose`, times in ISO 8601

`main(argv=None)` returns the exit status:

- `fleet economy FILLUPS --reg REG` prints one line per segment, `START-END L100`, as
  `10000-10600 6.00`, then `average 6.00`.
- `fleet due VEHICLES SERVICES --reg REG --today DATE --odometer KM` prints one line per item,
  `kind status due`, where due is the day, the km, or both joined by ` or `; exit 1 when an item
  is overdue.
- `fleet check TRIPS` prints `trip N: kind: detail` per problem, N counting from 1; exit 1 when
  there is any.
- `fleet costs VEHICLES FILLUPS SERVICES --reg REG --from DATE --to DATE` prints each `Costs` field
  as `name value`, one per line.

Bad input prints the error on stderr and exits 2; otherwise the exit status is 0.

## Usage

_To be written as each module lands: a short example per module and per subcommand._
