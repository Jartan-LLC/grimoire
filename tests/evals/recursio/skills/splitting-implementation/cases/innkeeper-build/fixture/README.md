# innkeeper

The back office of a small hotel: what rooms are free, which room each booking gets, what a stay
costs, what a cancellation costs, and who cleans which room today. A library and a command.

## Data model

`src/innkeeper/model.py` holds `RoomType`, `Room`, `Guest`, `Booking` (dates, room type, rate plan,
adults, children's ages, `BookingStatus`, and the room once assigned), `RatePlan`, `Season` and
`CENTS`. Money is always `Decimal`. Every module below works on these and on nothing else from its
siblings; only the command uses them all.

A booking covers the nights from check-in up to the night before check-out, a night being named by
the date it starts on. `CONFIRMED`, `CHECKED_IN` and `CHECKED_OUT` bookings occupy their nights;
`CANCELLED` and `NO_SHOW` bookings never do. Room numbers sort in natural order: digit runs compare
as numbers, so `2` comes before `10`, `10` before `10A`, and `10A` before `11`.

## Availability and room assignment (`innkeeper.availability`)

- `inventory(rooms) -> dict[str, int]`: the rooms of each type that are not out of order.
- `booked(bookings, room_type, night) -> int`: the bookings of that type occupying that night.
- `available(rooms, bookings, room_type, check_in, check_out, overbooking=None) -> int`: the
  smallest, over the stay's nights, of the inventory plus the overbooking allowance minus the
  bookings. It may be negative. `overbooking` maps a room type to an `int` number of rooms or to a
  `Decimal` fraction of its inventory, rounded down: `Decimal("0.1")` of 25 rooms allows 2. A
  check-out on or before the check-in raises `ValueError`.
- `grid(rooms, bookings, start, end, overbooking=None) -> dict[str, list[int]]`: the availability
  of every room type for each night from `start` up to `end`, types in code order.
- `assign_rooms(rooms, bookings, start, end) -> Assignment` gives a room to every occupying booking
  for each of its nights between `start` and `end`. `Assignment` holds `nights`, mapping a booking
  id to its list of `(night, room number or None)`, `moves`, mapping a booking id to the number of
  times it changes room, and `unassigned`, the `(booking id, night)` pairs no room could take,
  sorted.
  - A booking with a `room` keeps it on every night. Two such bookings in one room on one night
    raise `AssignmentError` naming both bookings and the night.
  - The rest go in order of check-in, then longer stays first, then booking id. Only rooms of the
    booking's type that are not out of order are used.
  - When some room is free on every night of the stay, the booking takes the best fit: the room
    with the fewest free nights directly before the stay (back to `start`) plus directly after it
    (up to `end`), ties going to the first room in natural order. This keeps long free runs whole.
  - Otherwise the stay is covered with as few moves as possible: from the first night, take the
    room that is free for the longest run from that night (ties in natural order), and go on from
    where that run ends. Nights no room is free for stay unassigned.

## Rates and quotes (`innkeeper.rates`)

`quote(booking, room_type, plan, seasons, surcharges=Surcharges()) -> Quote` and
`nightly_rates(...)`, with the same arguments, returning the `NightRate`s alone. A `NightRate` holds
`night`, `base` (the seasonal rate), `discount` (the amount taken off it), `surcharges` and
`total`; a `Quote` holds `nights`, `room_total`, `city_tax` and `total`. Every amount is rounded to
`CENTS` with `ROUND_HALF_UP`.

- **Seasonal rate**: the season of the booking's room type that covers the night. Friday and
  Saturday nights take the weekend rate, the rest the weekday rate. A night no season covers raises
  `RateError("no rate for DBL on 2026-12-24")`; two seasons of one type covering the same night
  raise `RateError` too.
- **Occupancy**: children aged 12 or more count as adults, for the limits and for the charges;
  children under 3 do not count toward the room's occupancy. More adults than `max_adults`, more
  adults and children aged 3 to 11 than `max_occupancy`, or no adult at all, raise `RateError`.
- **Surcharges**, per night and never discounted: `Surcharges.extra_adult` (default 30.00) for each
  adult beyond the type's `base_occupancy`, and `Surcharges.child` (default 15.00) for each child
  aged 3 to 11. Children under 3 stay free.
- **Discounts** on the seasonal rate only: 10 % for stays of 7 to 13 nights and 15 % for 14 nights
  or more, then the plan's `discount_pct`, applied one after the other:
  `base x (1 - stay) x (1 - plan / 100)`, then rounded. A 7-night stay at 99.99 on a 12 % plan pays
  79.19 a night before surcharges (99.99 x 0.9 x 0.88 = 79.19208).
- A stay shorter than the plan's `min_nights` raises `RateError`.
- **City tax**: 2.50 per guest aged 16 or more, adults included, for each of the first seven nights
  at most. It is not discounted and is not part of `room_total`.

Example: a `DBL` room with base occupancy 2 at 120.00 on weekdays and 150.00 at weekends, two adults
and a child of 5 from Friday 2026-07-03 to Monday 2026-07-06 on a plan with no discount: the nights
cost 165.00, 165.00 and 135.00, the room total is 465.00, the city tax 15.00 and the total 480.00.
On a 12 % plan the nights cost 147.00, 147.00 and 120.60.

## Cancellations (`innkeeper.cancellation`)

The functions take the stay's nightly totals, `nights`, as a list of `Decimal` in night order, so
this module does not depend on the rates module. The stay total is their sum.

- `cancellation_charge(booking, plan, nights, cancelled_at, tz, tiers=DEFAULT_TIERS,
  cutoff_hour=18) -> Decimal`. A `Tier` holds `days_before` and either `percent` of the stay total
  or a number of `nights`, charged as the first that many nightly totals. `DEFAULT_TIERS` are 14
  days 0 %, 7 days 25 %, 2 days 50 % and 0 days 1 night.
- A tier's deadline is `cutoff_hour`:00 wall-clock time in the hotel's IANA zone `tz` on the date
  `days_before` days before check-in. `cancelled_at` is timezone-aware and is compared in that
  zone. The cancellation takes the tier with the most days whose deadline it is strictly before;
  after every deadline it pays the whole stay.
- Example: a hotel in `Europe/Lisbon` (UTC+1 in summer) and a check-in on 2026-07-14. A
  cancellation at 2026-06-30T17:30Z is 18:30 local on 30 June, past the 14-day deadline, so it pays
  25 %.
- A non-refundable plan pays the whole stay whenever it cancels, except that any booking cancelled
  within one hour of its `created_at` pays nothing, unless check-in is less than 48 hours after the
  cancellation.
- Only a `CONFIRMED` booking can be cancelled; any other status raises `CancellationError`.
- `no_show_charge(booking, plan, nights) -> Decimal`: the first night for a refundable plan, the
  whole stay for a non-refundable one.
- `shorten_charge(booking, plan, nights, new_check_out, changed_at, tz, tiers=DEFAULT_TIERS,
  cutoff_hour=18) -> Decimal`: the charge for giving up the nights from `new_check_out` on, worked
  out by the same tiers as if those nights were a stay of their own starting on `new_check_out`.
  A non-refundable plan pays for all of them. `new_check_out` must be after check-in and before
  check-out, or `ValueError` is raised.
- `refund(paid, charge) -> Decimal` is what goes back to the guest, never below zero, and
  `balance_due(paid, charge) -> Decimal` what the guest still owes, never below zero.
- Percentages are rounded half-up to cents.

## Housekeeping (`innkeeper.housekeeping`)

`daily_tasks(day, rooms, bookings, service_every=2) -> TaskList` holds `tasks` and `warnings`. A
`Task` holds `room`, `floor`, `kind`, `credits` and `arrival_today`. Only occupying bookings with a
room count.

| Kind | When | Credits |
|------|------|---------|
| `departure` | a booking checks out of the room today | 3 |
| `linen` | a stay of 4 nights or more is on night k (k = days since check-in, k > 0) and k is a multiple of 3 | 2 |
| `stayover` | a stay is on night k, k > 0, k is a multiple of `service_every`, and no linen change is due | 1 |
| `inspect` | the room was empty last night and a booking checks in today | 1 |

- A departure task whose room also has an arrival today has `arrival_today` set, and that room gets
  no inspect task.
- An out-of-order room gets no tasks; a booking in it gets the warning
  `booking B7 is in out-of-order room 204`. A booking with no room gets `booking B7 has no room`.
  Two bookings occupying one room on last night or tonight get `room 101 double-booked on
  2026-07-04`.
- Tasks are sorted by floor, then natural room order.

`assign(tasks, housekeepers) -> Plan` shares the tasks out. A `Housekeeper` holds `name`, `floors`
and `capacity` in credits; a `Plan` holds `assignments`, mapping each housekeeper's name to their
tasks, and `unassigned`.

- Tasks are placed in priority order: departures with an arrival today, other departures, linen,
  stayovers, inspections; within a priority by floor and then natural room order.
- A task goes to the housekeeper who covers its floor and has the most spare capacity that still
  fits it, ties going to the name first in alphabetical order. When nobody covering the floor has
  room for it, it goes the same way to someone covering a floor one above or below, and then to
  anyone; failing that it is unassigned.
- Each housekeeper's tasks are listed by floor, then priority, then natural room order.

## Command (`innkeeper.cli`)

Every subcommand reads the hotel from one JSON file:

```json
{
  "hotel": {"name": "Casa Azul", "timezone": "Europe/Lisbon"},
  "room_types": [{"code": "DBL", "name": "Double", "base_occupancy": 2, "max_adults": 2, "max_occupancy": 3}],
  "rooms": [{"number": "101", "room_type": "DBL", "floor": 1, "out_of_order": false}],
  "rate_plans": [{"code": "FLEX", "name": "Flexible", "refundable": true, "discount_pct": "0", "min_nights": 1}],
  "seasons": [{"room_type": "DBL", "start": "2026-04-01", "end": "2026-10-31", "weekday_rate": "120.00", "weekend_rate": "150.00"}],
  "guests": [{"guest_id": "G1", "name": "Test Guest"}],
  "bookings": [{"booking_id": "B1", "guest_id": "G1", "room_type": "DBL", "rate_plan": "FLEX", "check_in": "2026-07-03", "check_out": "2026-07-06", "adults": 2, "children_ages": [5], "status": "confirmed", "created_at": "2026-05-01T09:00:00+00:00", "room": null}],
  "housekeepers": [{"name": "Ana", "floors": [1, 2], "capacity": 24}],
  "overbooking": {"DBL": 1}
}
```

Money is written as strings and read as `Decimal`; `out_of_order`, `discount_pct`, `min_nights`,
`room` and `overbooking` may be left out.

- `innkeeper quote DATA.json --type CODE --plan CODE --in DATE --out DATE --adults N [--child
  AGE]...` checks availability first and prints `not available` with status 1 when it is under 1.
  Otherwise it prints one line per night, `2026-07-03 Fri  150.00  +15.00  165.00` (date, weekday,
  base less discount, surcharges, total), then `room 465.00`, `city tax 15.00` and
  `total 480.00`, amounts right-aligned.
- `innkeeper availability DATA.json --from DATE --to DATE` prints the grid: one row per room type,
  one column per night headed `MM-DD`, numbers right-aligned.
- `innkeeper housekeeping DATA.json --date DATE` assigns rooms to the bookings around that day
  that have none, builds the day's tasks and shares them out, then prints for each housekeeper a
  heading `Ana (22/24 credits)` and one line per task, `101  departure  3  arrival` (the last word
  only for an arrival today), then `unassigned:` and its tasks if there are any. Warnings print to
  stderr.
- `innkeeper cancel DATA.json BOOKING_ID [--at DATETIME] [--paid AMOUNT]` prices the stay's nights
  with the rates module, then prints `charge`, `refund` and `balance due`. `--at` defaults to now
  and `--paid` to 0.

A data file that cannot be read or has a missing key, a bad date or a bad amount prints
`DATA.json: message` to stderr and exits 2. A `RateError`, `AssignmentError` or
`CancellationError` prints its message to stderr and exits 1.

## Status

Only the data model exists.
