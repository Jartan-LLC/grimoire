# transitkit

Reads a public-transport timetable in the GTFS text format, checks it, and answers two questions
riders ask: what leaves this stop next, and how do I get from here to there. A library and a
command.

## Data model

`src/transitkit/model.py` holds the records: `Stop`, `Route` with its `RouteType`, `Trip`,
`StopTime` (times in seconds after the service day's midnight, possibly past 24:00:00), `Service`
(weekday flags and a date range), `ServiceException` with its `ExceptionKind`, and `Feed`, which
holds lists of all of them. It also defines `SECONDS_PER_DAY` and `EARTH_RADIUS_M`. Every module
below works on these and on nothing else from its siblings; only the command uses them all. Each
module that needs a distance computes its own haversine distance with `EARTH_RADIUS_M`.

## Feed reader (`transitkit.feed`)

- `parse_time(text) -> int` reads `H:MM:SS` or `HH:MM:SS` with hours 0 to 47 and minutes and
  seconds 00 to 59: `parse_time("25:10:00") == 90600`. Anything else raises `ValueError`.
- `format_time(seconds) -> str` is the inverse, always with two-digit hours:
  `format_time(90600) == "25:10:00"`, `format_time(300) == "00:05:00"`.
- `read_feed(texts) -> FeedResult` takes a mapping from file name to file contents, and
  `read_feed_dir(path) -> FeedResult` reads the six files from a directory. `FeedResult` holds the
  `Feed` and a list of `LineError(file, line, message)`. The header is line 1 and data starts at
  line 2.

Every file is UTF-8, with a byte-order mark at its start dropped, and CSV as RFC 4180 has it:
fields in double quotes may hold commas, line breaks and doubled quotes. The header names the
columns, which are matched by name in any order; unknown columns are ignored and fields are
stripped of surrounding spaces. Blank lines are skipped. A data line with a bad or missing required
value is a line error and is skipped; reading goes on.

| File | Required columns | Read into |
|------|------------------|-----------|
| `stops.txt` | `stop_id`, `stop_name`, `stop_lat`, `stop_lon` | `Stop`; lat in -90..90, lon in -180..180 |
| `routes.txt` | `route_id`, `route_short_name`, `route_long_name`, `route_type` | `Route`; at least one name; type 0 to 4 |
| `trips.txt` | `route_id`, `service_id`, `trip_id` | `Trip`; optional `trip_headsign`, `direction_id` (0 or 1) |
| `stop_times.txt` | `trip_id`, `arrival_time`, `departure_time`, `stop_id`, `stop_sequence` | `StopTime`; sequence a non-negative integer |
| `calendar.txt` | `service_id`, `monday` to `sunday`, `start_date`, `end_date` | `Service`; flags `0` or `1`, dates `YYYYMMDD` |
| `calendar_dates.txt` | `service_id`, `date`, `exception_type` | `ServiceException`; type 1 or 2 |

- A stop time with only one of its two times takes it for both; with neither, or with a departure
  before its arrival, it is a line error.
- A second record with the same `stop_id`, `route_id`, `trip_id`, or `service_id` in
  `calendar.txt` is a line error (`duplicate stop_id S1`); the first is kept.
- `stops.txt`, `routes.txt`, `trips.txt` and `stop_times.txt` are required, and so is at least one
  of the two calendar files. A missing required file, or a file missing a required column, is a
  single error on line 0 (`missing column stop_lat`), and that file contributes nothing.
- Records keep file order, except `stop_times`, which is sorted by trip id and then sequence.

## Service calendar (`transitkit.calendar`)

- `active_services(feed, on) -> set[str]`: the services running on date `on`. A service runs when
  `on` is between its start and end and its weekday flag is set. An `ADDED` exception adds the date
  even outside the range, or for a service id with no `Service` record; a `REMOVED` exception
  removes it.
- `overnight_services(feed, on) -> set[str]`: the services active on the day before `on` that have
  at least one stop time at or after `SECONDS_PER_DAY`, so their trips are still running in the
  small hours of `on`.
- `service_dates(feed, service_id) -> list[date]`: every date the service runs, sorted, over the
  union of its range and its exception dates. An unknown id gives an empty list.
- `service_span(feed, on) -> tuple[int, int] | None`: the earliest departure and the latest arrival
  over the trips of the services active on `on`, in that day's seconds; None when nothing runs.
- `feed_dates(feed) -> tuple[date, date] | None`: the first and last date any service runs.
- `describe(service, exceptions) -> str`: a one-line summary of a service, its weekdays as runs of
  three-letter names, then its range, then the counts of added and removed dates when nonzero:
  `Mon-Fri 2026-01-05..2026-06-30, +2 added, -3 removed`, `Sat, Sun 2026-01-03..2026-06-28`,
  `daily 2026-01-01..2026-12-31`, and `no regular days` when no flag is set. A run is three or more
  consecutive days; shorter runs list each day, separated by a comma and a space.

## Validation (`transitkit.validate`)

`validate(feed) -> list[Issue]`, where `Issue` holds `severity` (`error` or `warning`), `file`,
`ref` (the id the issue is about), `code` and `message`. Issues are sorted by severity (errors
first), then file, then ref, then code.

| Code | Severity | File | Finding |
|------|----------|------|---------|
| `unknown_route` | error | trips.txt | a trip's route id is not in the routes |
| `unknown_service` | error | trips.txt | a trip's service id has neither a `Service` nor any exception |
| `unknown_trip` | error | stop_times.txt | a stop time's trip id is not in the trips |
| `unknown_stop` | error | stop_times.txt | a stop time's stop id is not in the stops |
| `duplicate_sequence` | error | stop_times.txt | two calls of one trip share a stop_sequence |
| `decreasing_time` | error | stop_times.txt | a call arrives before the previous call departs; equal times are allowed |
| `too_few_stops` | error | trips.txt | a trip has fewer than two calls |
| `fast_travel` | warning | stop_times.txt | the speed between consecutive calls exceeds the route type's limit |
| `unused_stop` | warning | stops.txt | no stop time calls at the stop |
| `unused_route` | warning | routes.txt | no trip runs on the route |
| `no_service_day` | warning | calendar.txt | the service runs on no date at all, exceptions included |

- Speed is the haversine distance between the two stops over the time from the earlier call's
  departure to the later call's arrival. The limits in km/h are tram 100, subway 150, rail 500,
  bus 120 and ferry 80. When that time is zero, the hop is too fast only if the stops are more than
  100 m apart. A trip whose route is unknown is not speed-checked.
- The message names the record and the problem: `trip T7: route R9 is not in routes.txt`,
  `trip T7: 1.9 km from S3 to S4 in 0 s`, `trip T7: 212 km/h from S3 to S4, limit 120`.
- `ref` is the trip id for the trip and stop-time checks and the stop, route or service id for the
  others.

## Departures (`transitkit.departures`)

The functions take the active service ids as arguments, so this module does not depend on the
calendar: `today` is the set of services running on the day asked about and `yesterday` the set
running the day before.

- `next_departures(feed, stop_id, today, yesterday, after, count=5, route_ids=None, within=None)
  -> list[Departure]`. `Departure` holds `trip_id`, `route_id`, `route_short_name`, `headsign`,
  `departure` (seconds of today) and `from_yesterday`. A trip of a `today` service departs at its
  stop time. A trip of a `yesterday` service with a departure at or after `SECONDS_PER_DAY` departs
  today at that time less `SECONDS_PER_DAY`, with `from_yesterday` true. Departures at or after
  `after` count; with `within`, only those before `after + within`. A trip's last call is not a
  departure. With `route_ids`, only those routes. Sorted by departure, then route short name, then
  trip id; the first `count`. An unknown stop raises `KeyError`.
- The headsign is the trip's own, or else the name of the trip's last stop.
- `board(feed, stop_id, today, yesterday, after, per_line=3) -> list[BoardLine]`: the next
  departures grouped by route and headsign, each `BoardLine` holding `route_short_name`, `headsign`
  and up to `per_line` departure times. Lines sort by route short name in natural order (`2`
  before `10` before `N1`: digit runs compare as numbers), then headsign.

## Journey planner (`transitkit.planner`)

`earliest_arrival(feed, services, origin, destination, depart_at, min_transfer=120,
walk_radius=400.0, walk_speed=1.25, max_transfers=None) -> Journey | None` finds the earliest
arrival with the Connection Scan Algorithm over the trips of the given service ids. Like the
departures module it takes the active services as an argument.

- A connection is one hop of a trip from one call to the next, departing at the earlier call's
  departure and arriving at the later call's arrival. Connections are scanned once, sorted by
  departure.
- Staying on the same trip needs no transfer time. Boarding a different trip at the stop where one
  has just been left needs `min_transfer` seconds between the arrival and the departure. The
  journey's first boarding needs none.
- Footpaths join every pair of distinct stops within `walk_radius` metres. Walking takes the
  distance over `walk_speed`, rounded up to whole seconds, and replaces the transfer time at the
  far stop. A journey may start or end with a walk.
- `Journey` holds `departure`, `arrival` and `legs`. A `Leg` holds `kind` (`ride` or `walk`),
  `trip_id` (None for a walk), `from_stop`, `to_stop`, `depart` and `arrive`. Consecutive hops on
  one trip form one ride leg. Of two journeys with the same arrival, the one with fewer ride legs
  wins; then the one that departs later.
- `max_transfers` caps the number of ride legs minus one.
- Origin equal to destination gives a journey with no legs that arrives at `depart_at`. No journey
  gives None. An unknown stop raises `KeyError` naming it.

## Command (`transitkit.cli`)

- `transitkit validate FEED_DIR` prints one line per issue, `severity file ref code: message`, and
  then `N errors, M warnings`. The exit status is 1 when there is any error.
- `transitkit departures FEED_DIR STOP_ID [--date YYYY-MM-DD] [--time HH:MM] [--count N]
  [--route ID]...` finds today's and yesterday's services with the calendar module and prints one
  line per departure: `HH:MM  route  headsign`, with times of 24:00 or later printed less 24 hours.
  `--date` and `--time` default to now in the local zone.
- `transitkit plan FEED_DIR FROM TO [--date YYYY-MM-DD] [--time HH:MM] [--min-transfer SECONDS]
  [--walk METRES]` prints each leg, `HH:MM STOP -> HH:MM STOP  route` for a ride (the route's short
  name) and `walk` in place of the route for a walk, then `arrive HH:MM, N transfers`. With no
  journey it prints `no journey` and exits 1.

Feed line errors print to stderr as `FILE:LINE: message` and the command carries on, ending with
status 1. A feed directory that cannot be read or lacks a required file exits 2.

## Status

Only the data model exists.
