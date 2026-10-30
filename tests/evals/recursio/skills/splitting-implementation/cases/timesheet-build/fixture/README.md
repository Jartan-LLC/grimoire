# timesheet

Turns time-tracking exports and calendars into overtime reports and client invoices, as a
TypeScript library and a command. Node 24 runs the `.ts` files directly (type stripping); there are
no dependencies, and time zones come from the `Intl` API Node ships with.

## Types

`src/types.ts` holds the shared records: `Entry` (one stretch of work in local time, with the real
minutes it lasted), `Holiday`, `Region` and `REGIONS`, `Rate`, and `LineError` and `ImportResult`.
Each module below imports only these, never a sibling; the command is the one piece that uses
them all.

## Importers (`src/importers.ts`)

Both importers return an `ImportResult`. A bad record becomes a `LineError` numbered from 1 (the
record's first line) and is skipped. Both compute `minutes` from the zone: a local time that does
not exist (the spring-forward hour) is a line error, and an ambiguous one (the fall-back hour)
takes the earlier, summer-time instant.

- `importCsv(text, { zone, person?, dayFirst = false })` reads time-tracker CSV exports.
  - The delimiter is whichever of `,`, `;` and tab occurs most in the header line. Fields follow
    RFC 4180: quoted fields may hold the delimiter, `""` and line breaks.
  - Headers are matched trimmed and case-insensitively, in any order, extra columns ignored:
    person `Person`, `Name`, `Employee` or `User`; project `Project`, `Client/Project` or `Job`;
    `Date` or `Day`; start `Start`, `Start time` or `From`; end `End`, `End time` or `To`;
    duration `Duration`, `Hours` or `Time`; `Billable` or `Billable?`; zone `Time zone` or `TZ`;
    note `Description`, `Notes` or `Note`. A missing person column needs the `person` option, a
    missing zone column uses `zone`; no date or no project column is a single error on line 1
    and no entries.
  - Dates are `2026-10-12`, or with slashes `10/12/2026` (month first) or, with `dayFirst`,
    `12/10/2026`. Times are `14:05` or `2:05 PM`, `12:00 AM` being midnight.
  - Durations: `1:30` (hours and minutes), `1.5` or `1.5h` (decimal hours), `90m`, `1h 30m` and
    `2h`. A negative or empty duration is an error.
  - A row gives start and end (an end at or before the start runs into the next day), or start
    and duration (the end follows from it), or date and duration alone (starting at 09:00). When
    start, end and duration are all given and disagree by more than one minute, it is an error.
  - Billable takes `yes`, `no`, `y`, `n`, `true`, `false`, `1` and `0` in any case; empty is
    billable, anything else is an error.
- `importIcs(text, { person, zone })` reads iCalendar (RFC 5545) files.
  - Lines end in CRLF or LF. A line starting with a space or tab continues the previous one, with
    that one character removed, before anything else is parsed.
  - Each `BEGIN:VEVENT` ... `END:VEVENT` block is one entry. `DTSTART;TZID=Europe/Berlin:20261012T090000`
    is local to that zone; `DTSTART:20261012T070000Z` is UTC and converted to the `zone` option's
    local time; a floating `DTSTART:20261012T090000` is local to `zone`. The end is `DTEND` in
    the same forms, or `DURATION` as `PT1H30M`, `PT45M` or `P1DT2H`.
  - `SUMMARY` of `Atlas: sprint review` gives the project `Atlas` and the note `sprint review`;
    a summary with no colon is the project with an empty note. Text values unescape `\,`, `\;`,
    `\n` and `\\`.
  - `CATEGORIES` containing `non-billable` (any case) makes it non-billable.
  - Events with `STATUS:CANCELLED`, all-day events (`VALUE=DATE`) and `TRANSP:TRANSPARENT` are
    skipped without an error. An `RRULE` is the error `recurring events are not supported`; a
    missing `DTSTART`, an unknown `TZID` or an end before the start is an error on the
    `BEGIN:VEVENT` line.

## Holidays (`src/holidays.ts`)

- `easter(year)` returns Easter Sunday as `YYYY-MM-DD` by the anonymous Gregorian computus
  (Meeus, Jones and Butcher): 2026-04-05, 2027-03-28, 2038-04-25.
- Rules come in four kinds: a fixed date (`{ month, day }`), the nth weekday of a month (third
  Monday of January), the last weekday of a month (last Monday of May), and an offset from Easter
  in days (Good Friday is -2). Each rule also names how it moves off a weekend:
  - `none`: it stays where it falls.
  - `nearest`: Saturday moves to the Friday before, Sunday to the Monday after (US).
  - `next-free`: Saturday or Sunday moves to the next weekday that is not already a holiday, so a
    Christmas on Saturday is observed Monday the 27th and Boxing Day on Sunday Tuesday the 28th
    (GB-ENG).
- The regions:
  - `US`, federal holidays: New Year's Day (Jan 1, nearest), Martin Luther King Jr. Day (3rd Mon
    Jan), Washington's Birthday (3rd Mon Feb), Memorial Day (last Mon May), Juneteenth (Jun 19,
    nearest), Independence Day (Jul 4, nearest), Labor Day (1st Mon Sep), Columbus Day (2nd Mon
    Oct), Veterans Day (Nov 11, nearest), Thanksgiving (4th Thu Nov), Christmas Day (Dec 25,
    nearest).
  - `GB-ENG`, bank holidays in England and Wales: New Year's Day (Jan 1), Good Friday, Easter
    Monday, Early May bank holiday (1st Mon May), Spring bank holiday (last Mon May), Summer bank
    holiday (last Mon Aug), Christmas Day (Dec 25), Boxing Day (Dec 26); the fixed ones
    `next-free`.
  - `DE-BY`, Bavaria: New Year's Day, Epiphany (Jan 6), Good Friday, Easter Monday, Labour Day
    (May 1), Ascension Day (+39), Pentecost Monday (+50), Corpus Christi (+60), Assumption Day (Aug
    15), German Unity Day (Oct 3), All Saints' Day (Nov 1), Christmas Day, St Stephen's Day (Dec
    26); none move.
  - `FR`: New Year's Day, Easter Monday, Labour Day (May 1), Victory in Europe Day (May 8),
    Ascension Day, Pentecost Monday, Bastille Day (Jul 14), Assumption Day, All Saints' Day,
    Armistice Day (Nov 11), Christmas Day; none move.
- `holidays(region, year)` returns that year's `Holiday`s sorted by observed date. A holiday
  belongs to the year of its actual date even when observed in the year before (US New Year's
  Day 2028 falls on a Saturday and is observed 2027-12-31). An unknown region or a year outside
  1900-2199 throws `RangeError`.
- `holidaysBetween(region, from, to)` returns those observed in the inclusive date range, across
  years, and `isHoliday(region, date)` the one observed on a date, or null.

## Overtime (`src/overtime.ts`)

`computeOvertime(entries, holidays, rules = DEFAULT_RULES)` returns
`{ people: [{ person, weeks: [{ week, days, totals }] }], warnings }`, people sorted by name,
weeks by ISO week (`2026-W42`, Monday first), days by date. Each day holds `date`, `worked`,
`breakMinutes`, `regular`, `ot15`, `ot20` and `holiday`, all whole minutes. Billable or not, every
entry counts. An entry belongs to the local date it starts on.

- **Overlaps**: two entries of one person that overlap give a warning naming both, and the later
  one's overlapping minutes are not counted.
- **Breaks**: a day of more than 6 h worked loses an unpaid 30 minutes, more than 9 h loses 45,
  less the gaps between that day's entries: gaps of 30 minutes or more on a 7-hour day leave
  nothing to deduct.
- **Daily**: after breaks, minutes beyond 8 h in a day are `ot15` (1.5x) and beyond 12 h `ot20`
  (2x).
- **Weekly**: regular minutes beyond 40 h in a week become `ot15`, taken from the latest day of
  the week backwards. Minutes already daily overtime do not count toward the 40 h.
- **Seventh day**: a person who works all seven days of an ISO week has the Sunday's first 8 h as
  `ot15` and the rest as `ot20`, in place of the daily rule.
- **Holidays**: minutes on a day in `holidays` are all `holiday` (2x), whatever the other rules
  say, and do not count toward the 40 h.
- `rules` can change every threshold and multiplier: `dailyOt15`, `dailyOt20`, `weekly`,
  `breaks` (a list of `{ afterMinutes, breakMinutes }`), `seventhDay` (on or off).
- `payableHours(totals, rules)` is regular + 1.5 x ot15 + 2 x ot20 + 2 x holiday, in hours to two
  decimal places.

## Invoicing (`src/invoice.ts`)

- `rateFor(rates, person, project, date)` picks the most specific `Rate` in effect on the date:
  person and project, then project only, then person only, then the default with neither. At one
  level the rate with the latest `from` wins. No rate throws `RangeError` naming person, project
  and date.
- `roundMinutes(minutes, increment, mode)` with increments of 6 or 15 minutes, mode `up` or
  `nearest` (half up). In 6-minute steps 7 minutes is 12 up and 6 nearest; in 15-minute steps 22
  minutes is 30 up and 15 nearest, and 0 stays 0.
- `buildInvoice(entries, rates, options)` bills the billable entries in `options.month`
  (`YYYY-MM`, by local start date) for `options.projects` (or all). With `per: "entry"` each entry
  rounds on its own; with `per: "day"` each person's minutes per project and day add up first and
  round once. A line per project and person, sorted by project then person, carries the rounded
  hours, the rate and amount = round(minutes x hourly / 60), half up, in minor units. An entry
  whose rate changes mid-month uses the rate on its own date, which can give one person two
  lines.
- Caps: `options.caps` as `[{ project, maxHours?, maxAmount? }]` per month. Hours past the cap are
  not billed, taken from the latest entries first, and appear in `writtenOff` with their amount.
- `subtotal`, `tax` (`options.taxPercent`, rounded half up) and `total`. Rates in two currencies
  on one invoice throw `RangeError`.
- `formatMoney(amount, currency, locale)` from minor units: `en` gives `USD 1,234.50`, `de`
  `1.234,50 EUR`, `fr` `1 234,50 EUR` (a plain space), a negative amount a leading `-`. `JPY`
  has no minor unit, so 1235 is `JPY 1,235`.

## Command (`src/cli.ts`)

The `timesheet` bin runs `src/cli.ts`. Files ending `.csv` go to the CSV importer and `.ics` to
the calendar one; `--zone` (default `UTC`) is their zone and `--person` the person for files that
lack one.

- `timesheet report FILE... [--region US|GB-ENG|DE-BY|FR] [--from DATE] [--to DATE] [--json]`
  prints per person and week a table of days with the columns Date, Worked, Break, Regular,
  1.5x, 2x and Holiday as `h:mm`, a totals row with payable hours, and the holidays of the
  range under the table. Without `--region` no day is a holiday.
- `timesheet invoice FILE... --rates FILE --month YYYY-MM [--project NAME]... [--round 6|15]
  [--per entry|day] [--mode up|nearest] [--tax PCT] [--locale en|de|fr] [--json]` prints the
  invoice: one line per project and person, then subtotal, tax and total, then any written-off
  hours. The rates file is a JSON array of `Rate`s. Defaults: `--round 6 --per entry --mode up`.

Line errors print to stderr as `FILE:LINE: message`, overlap warnings as `warning: ...`. The exit
status is 0, or 1 when any file had line errors, or 2 for a usage error, an unreadable file, an
unknown extension or a missing rate; the other files are still read.

## Status

Only `src/types.ts` exists.
