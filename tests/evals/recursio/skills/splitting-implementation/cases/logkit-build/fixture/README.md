# logkit

Reads web and application logs, cuts them into time windows, checks alert rules against the
windows, and prints the results, as a TypeScript library and a command. Node 24 runs the `.ts`
files directly; there are no dependencies.

## Types

`src/types.ts` holds what the modules pass to one another: `LogRecord` (one line from any format),
`Level` and `LEVELS`, `LineError` and `IngestResult` (a parser's output), `WindowStats` (one time
window), and `AlertState` and `AlertEvent` (an alert rule changing state). Each module below
imports these and nothing from its siblings; only the command uses them all.

## Ingest (`src/ingest.ts`)

Three parsers, each `(lines: string[], source: string) => IngestResult`. Records come in input
order; a line that cannot be read becomes a `LineError` numbered from 1 and is skipped. Blank lines
are skipped silently.

- `parseNginx`: the combined format with an optional request time appended:
  `$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer"
  "$http_user_agent" $request_time`, for example
  `203.0.113.7 - - [11/Oct/2026:13:55:36 -0700] "GET /api/books?page=2 HTTP/1.1" 200 5120 "-" "curl/8.5.0" 0.123`.
  `time_local` is `dd/Mon/yyyy:HH:MM:SS +hhmm` with English month abbreviations; an unknown month
  or impossible date is a line error. The message is the request string; the path is its second
  word without the query string (`/api/books`). A request that is not three words (`"-"`, or a
  probe's garbage) keeps the record with no path. `$body_bytes_sent` of `-` is 0 bytes;
  `$request_time` is seconds, so `0.123` is a latency of 123 ms (rounded to the nearest ms). The
  level is `error` for a 5xx status, `warning` for 4xx, `info` otherwise. Fields: `remote`,
  `method`, `protocol`, `referer` and `agent`, each left out when it is `-`. A status that is not
  three digits is a line error.
- `parseSyslog`: RFC 5424, `<PRI>1 TIMESTAMP HOSTNAME APP-NAME PROCID MSGID STRUCTURED-DATA [MSG]`,
  for example
  `<165>1 2026-10-11T22:14:15.003Z web01 api 4123 ID47 [req@32473 status="503" latency_ms="912"] upstream timed out`.
  The severity is PRI modulo 8: 0 to 2 are `critical`, 3 `error`, 4 `warning`, 5 `notice`, 6 `info`,
  7 `debug`; PRI above 191 or a version other than 1 is a line error. The timestamp is RFC 3339
  with up to six fraction digits and `Z` or an offset; the NILVALUE `-` there is a line error,
  since every record needs a time. The source is APP-NAME, or HOSTNAME when APP-NAME is `-`, or the
  `source` argument when both are. HOSTNAME, PROCID and MSGID go in fields as `host`, `procid` and
  `msgid` unless they are `-`. STRUCTURED-DATA is `-` or one or more `[id name="value" ...]`
  elements; inside a value `\"`, `\\` and `\]` are escapes. Each parameter becomes the field
  `id.name` (`req@32473.status`); a parameter named `status`, `latency_ms`, `bytes` or `path` in any
  element also sets the record's own property. An unterminated element is a line error. The
  message is MSG with a leading byte-order mark dropped, or empty.
- `parseLogfmt`: `key=value` pairs separated by spaces, for example
  `ts=2026-10-11T22:14:15Z level=warn msg="slow query" path=/api/books latency=1.2s rows=40`.
  A value is bare or double-quoted with `\"` and `\\` escapes; a key with no `=` has the value
  `"true"`; a repeated key keeps its last value. Lines starting with `#` are comments. The time is
  `ts` or else `time`, RFC 3339; a line with neither is a line error. `level` takes the six levels
  and the aliases `dbg`, `warn`, `err`, `crit` and `fatal`; missing means `info`, anything else is a
  line error. `msg` is the message. `latency` is a number with the unit `us`, `ms` or `s`, or bare
  meaning ms (`1.2s` is 1200 ms). `status`, `bytes` and `path` set the record's own properties;
  other keys go in fields. An unterminated quote is a line error.

`detectFormat(line)` returns `"nginx"`, `"syslog"` or `"logfmt"` for a format's first line, or null:
a line opening with `<`, digits and `>1` is syslog, one opening with an IP address, a dash and a
`[` further on is nginx, and one opening with `key=` is logfmt.
`ingest(text, source)` splits on `\n` or `\r\n`, detects the format from the first non-blank line,
and runs that parser; with no format detected it returns one line error, `unknown log format`.

## Window statistics (`src/stats.ts`)

- `percentile(values, p)`: the nearest-rank percentile: sort ascending and take the value at rank
  ceil(p / 100 x n), counting from 1; p = 0 is the smallest; an empty list is null. Of
  `[100, 200, 300, 400, 500]` p50 is 300 and p95 is 500.
- `windows(records, sizeMs, options?)` returns `WindowStats[]` for tumbling windows aligned to the
  epoch: a record belongs to the window starting at floor(at / sizeMs) x sizeMs, and `end` is
  start + sizeMs. Records may come in any order. The windows run from the first record's window to
  the last record's, empty ones included (count 0, error rate 0, percentiles null, no top paths).
  No records gives no windows. `options.topN` (default 5) and `options.source` (keep only that
  source) adjust it.
- Latency percentiles p50, p95 and p99 come from the records with a latency; `bytes` is their sum.
- Status classes count the records with a status by its hundreds digit; a status outside 100 to
  599 counts as `other`. Every class key is present, 0 when unused.
- A record is an error when its status is 500 or more, or, when it has no status, its level is
  `error` or `critical`. `errorRate` is errors / count over all the window's records.
- `topPaths` holds the `topN` most requested paths, most first, ties broken by path in ascending
  code-unit order; records with no path are not counted.
- `parseDuration(text)`: `90s`, `5m`, `1h`, `1h30m` or `250ms` to milliseconds; anything else
  throws `RangeError` naming the text.

## Alerts (`src/alerts.ts`)

A rule is one line of a small language:

```text
error_rate > 5% for 5m
p95(latency) > 800ms for 10m
rate(5xx) >= 2% for 3m
count < 10 for 15m
```

The metric is `error_rate`, `count`, `rate(1xx)` to `rate(5xx)` (that class's share of the
records with a status), or `p50(latency)`, `p95(latency)` or `p99(latency)`. The operator is `>`,
`>=`, `<` or `<=`. The threshold is a number with an optional unit: `%` only for `error_rate` and
`rate(...)` (without it the threshold is a fraction from 0 to 1), `ms` or `s` only for latency
(bare means ms), none for `count`. The duration after `for` is a positive whole number of `s`, `m`
or `h`. Tokens may be separated by any spaces.

- `parseRule(text, name)` returns a `Rule` (`name`, `metric`, `op`, `threshold` in the metric's own
  units, `forMs`) or a `RuleError` (`column`, counted from 1, at the offending token, and
  `message`). Messages name what was expected: `unknown metric "latency"`, `expected an operator`,
  `unit % does not apply to p95(latency)`, `threshold above 100%`, `expected "for"`,
  `duration must be positive`, `unexpected "x" after the duration`.
- `parseRules(text)` reads one `name: rule` per line, skipping blank lines and `#` comments, and
  returns `{ rules, errors }` with `LineError`s whose message starts with the column
  (`col 16: unit % does not apply to p95(latency)`). A repeated name is an error on its second line.
- `evaluate(rule, windows)` walks the windows in start order and returns the `AlertEvent`s, each at
  a window's `end` with that window's metric value. A window with no data for the metric (no
  records for a rate, no latencies for a percentile) never meets the condition. The states:
  - `inactive` -> `pending` on the first window that meets the condition.
  - `pending` -> `firing` once the condition has held over consecutive windows for at least
    `forMs`, measured from the start of the first of them to the end of the current one. When one
    window already covers `forMs`, the rule goes straight to `firing` with no `pending` event.
  - `pending` -> `inactive` (an event) on a window that does not meet it.
  - `firing` -> `resolved` on a window that does not meet it; `resolved` becomes `inactive` on the
    next window without an event, or `pending` again if that window meets the condition.
- `evaluateAll(rules, windows)` returns every rule's events sorted by `at`, then rule name.
- `finalStates(events)` returns a map of rule name to its last state (`inactive` when a rule had
  no events).

## Rendering (`src/render.ts`)

Every renderer returns a string ending in one newline. Times print in UTC.

- `renderSummary(windows, format)` with `format` one of `"text"`, `"json"` or `"markdown"`.
  - Text: a table with the columns Window (start as `YYYY-MM-DD HH:MM`), Count, Err%, p50, p95,
    p99, 2xx, 4xx, 5xx and Top path. Each column is as wide as its widest cell, columns are two
    spaces apart, numbers are right-aligned and text left-aligned. Err% has one decimal place,
    latencies are whole ms, a null is `-`, and Top path is `path (count)` of the first entry. A
    footer line follows: `12 windows of 5m, 3,402 records, 1.8% errors`, the count with thousands
    separators and the duration from `formatDuration`.
  - JSON: an array of objects with the keys `start`, `end` (ISO 8601), `count`, `errors`,
    `errorRate`, `p50`, `p95`, `p99`, `bytes`, `statusClasses` and `topPaths` in that order, two
    spaces of indentation, nulls kept.
  - Markdown: a GitHub table with the text columns, `---:` alignment for number columns, and `|`
    inside a path escaped as `\|`.
- `renderAlerts(events, format)`, same three formats. Text has one line per event:
  `2026-10-11T22:15:00Z  firing    high-errors  error_rate=7.2%`, the state padded to 8 characters.
  Values print by metric: rates and error rate as a percentage with one decimal, latencies as
  `912ms`, counts as whole numbers, no data as `no data`. With no events the text is
  `no alerts`.
- `formatDuration(ms)`: the largest units that fit, `1h30m`, `5m`, `1m30s`, `45s`, `250ms`; 0 is
  `0s`.

## Command (`src/cli.ts`)

The `logkit` bin runs `src/cli.ts`.

- `logkit summary [--window 5m] [--top N] [--source NAME] [--format text|json|markdown] FILE...`
  ingests every file, takes the windows of all their records together, and prints the summary.
  Each record's source defaults to the file's name without its extension. For each file it prints
  `FILE: N records, M bad lines` to stderr.
- `logkit alerts --rules FILE [--window 1m] [--format text|json|markdown] [--fail-on-firing] FILE...`
  parses the rules, evaluates them on the windows, and prints the events. With `--fail-on-firing`
  it exits 3 when any rule's final state is `firing`.

Line errors print to stderr as `FILE:LINE: message`. The exit status is 0, or 1 when any log line
was bad, or 2 for a usage error, an unreadable file, a file of unknown format or any rule error
(rule errors print as `RULES:LINE: message` and nothing is evaluated). Other log files are still
read after a bad one.

## Status

Only `src/types.ts` exists.
