# subtool

Reads and writes subtitle files in SubRip, WebVTT and Advanced SubStation Alpha, fixes their
timing and lays out their lines, as a library and a command. Written in TypeScript that Node 24 runs
directly (erasable syntax only: no `enum`, no `namespace`, no parameter properties; imports name
the `.ts` file). No npm dependencies.

## Contract

`src/types.ts` holds what the modules pass to one another: `Cue`, `Position`, `Style`, `Region`,
`Track`, `ParseError`, `ParseResult`, `Format` and `Align` with their `FORMATS` and `ALIGNMENTS`,
and `DEFAULT_LIMITS`. Cue text keeps only `<i>`, `<b>` and `<u>` as markup, so any reader's output
goes to any writer. Each module below uses only these and nothing of its siblings; only the command
uses them all.

Readers never throw on bad input: they return a `ParseResult` with every cue they could read and a
`ParseError` for each block they skipped, numbered by the block's first line. Writers return the
file's text ending in one newline, cues in start order (then end order, stable).

## SubRip (`src/srt.ts`)

- `parseSrt(text)`: a UTF-8 byte order mark is dropped; CRLF, LF and lone CR all end lines. Blocks
  are separated by one or more blank lines (whitespace-only counts as blank).
- A block is an index line (a positive integer, kept as `id`; indices need not be in order), a
  timing line `00:01:02,345 --> 00:01:04,000`, then one or more text lines. A block that starts
  with its timing line is accepted with no `id`. Hours have two or more digits, minutes and
  seconds two (under 60), milliseconds three; a `.` for the `,` is accepted. Anything after the end
  time (old `X1:` coordinates) is ignored.
- Errors, each skipping its block: a bad timing line, an end before the start (`end 00:00:01,000 is
  before start 00:00:02,000`), a block with no text lines, a block that is only an index.
- Markup: `<i>`, `<b>`, `<u>` and their closing tags are kept, case-folded to lower case;
  `<font ...>` and `</font>` are removed, their text kept. A leading `{\an8}` on the first line
  sets `position` to center, line `0%`; `{\an1}` to `{\an9}` map as in the ASS section; other
  `{\...}` blocks are removed.
- `writeSrt(track, { crlf = false })`: blocks numbered from 1, a blank line between them,
  timestamps as `HH:MM:SS,mmm` (hours past 99 written in full). Tags are written as kept; a
  position with line `0%` becomes a leading `{\an8}`.
- `formatSrtTime(ms)` and `parseSrtTime(text)` are exported too; the second returns `null` for a
  bad timestamp.

## WebVTT (`src/vtt.ts`)

- `parseVtt(text)`: the first line, after an optional byte order mark, must be `WEBVTT` alone or
  followed by a space or tab and any text; otherwise the result is an empty track and the error
  `missing WEBVTT header` on line 1. Lines up to the first blank line that look like `Key: value`
  go to `metadata` (`Kind: captions`, `Language: en`).
- `NOTE` blocks are comments, skipped up to the next blank line. A `STYLE` block's text goes to
  `css`; a `STYLE` block after the first cue is an error and skipped. A `REGION` block's
  `key:value` settings (`id:fred width:40% lines:3 regionanchor:0%,100% viewportanchor:10%,90%
  scroll:up`) become a `Region`; one without an `id` is an error.
- A cue is an optional identifier line (any line without `-->`), a timing line and text lines up to
  the next blank line. Timestamps are `[HH:]MM:SS.mmm`, hours optional and two or more digits when
  present. A text line containing `-->` is an error and skips the cue.
- Cue settings follow the end time, separated by spaces: `vertical:rl|lr`, `line:N` or `line:N%`
  with an optional `,start|center|end`, `position:N%` with an optional
  `,line-left|center|line-right`, `size:N%`, `align:start|center|end|left|right`, `region:id`.
  They fill `position` (align defaults to center). An unknown or malformed setting is ignored, as
  the WebVTT spec says, not an error.
- Text: `&amp;`, `&lt;`, `&gt;`, `&quot;`, `&apos;`, `&lrm;`, `&rlm;` and `&nbsp;` are decoded
  (`&nbsp;` to the no-break space character); an unknown entity stays as written. `<i>`, `<b>`
  and `<u>` are kept; `<c.class>`, `<v Name>`, `<lang en>`, `<ruby>`, `<rt>` and their closers are
  removed with their text kept, and so are inline timestamps such as `<00:00:01.500>`.
- `writeVtt(track)`: `WEBVTT`, the metadata lines, a blank line, each `css` entry as a `STYLE`
  block and each region as a `REGION` block, then the cues: `id` if any, the timing line with
  hours always written (`00:01:02.003 --> 00:01:04.000`) and settings in the order vertical, line,
  position, size, align, region (align only when not center), then the text with `&`, `<` and `>`
  escaped except in the kept tags.

## Advanced SubStation Alpha (`src/ass.ts`)

- `parseAss(text)`: sections start at `[Name]` lines. `[Script Info]` lines `Key: Value` go to
  `metadata`. `[V4+ Styles]` (or the older `[V4 Styles]`) and `[Events]` are read; `[Fonts]`,
  `[Graphics]` and any other section are skipped. Lines starting with `;` are comments.
- Style and event lines are read by their section's `Format:` line: field names matched
  case-insensitively, values trimmed. The last field (`Text`) takes the rest of the line, commas
  and all. A `Style:` or `Dialogue:` line before its section's `Format:` line is an error.
- Styles: `PrimaryColour` is `&HAABBGGRR` (`&H0000FFFF` is yellow, `#FFFF00`, alpha 0); `Bold`,
  `Italic` and `Underline` are `-1` for true and `0` for false; `Alignment` is the numpad 1-9 in
  V4+, and in V4 the legacy values 1-3 (bottom), 5-7 (top) and 9-11 (middle) are converted.
- Events: `Dialogue:` lines become cues; `Comment:` lines are skipped. `Start` and `End` are
  `H:MM:SS.cc` in centiseconds (`0:01:02.34` is 62340 ms). Cues come out sorted by start;
  `Layer` is ignored, and cues on different layers at the same time are all kept.
- Text: `\N` is a line break; `\n` is a space unless the script's `WrapStyle` is 2, when it is a
  break too; `\h` is a no-break space. In override blocks `{...}`: `\i1` and `\i0` become `<i>` and
  `</i>`, `\b1`/`\b0` and `\u1`/`\u0` likewise; `\r` closes what is open; `\an1` to `\an9` set the
  position, the column giving align (1, 4, 7 left; 2, 5, 8 center; 3, 6, 9 right) and the row the
  line (1-3 none, 4-6 `50%`, 7-9 `0%`); `\pos(x,y)` sets position to `x / PlayResX` and line to
  `y / PlayResY` as whole percents, with the defaults 384 and 288 when Script Info has none. Every
  other override (`\fad`, `\c&H...&`, `\fs`, `\k`, `\blur`) is removed. Text between `\p1` and
  `\p0` is a drawing and dropped. Tags still open at the end of a line are closed there. A `{`
  without a `}` is an error and skips the event.
- A cue whose style is italic has each line wrapped in `<i>...</i>` unless it starts with `\i0`.
- `writeAss(track, { playResX = 1920, playResY = 1080 })`: `[Script Info]` with `ScriptType:
  v4.00+`, the two PlayRes values and `Title` from metadata; `[V4+ Styles]` with the full V4+
  `Format:` line (Name through Encoding) and the track's styles, or one `Default` style (Arial 48,
  white, bottom center, margins 10, 10 and 10) when it has none; `[Events]` with `Format: Layer,
  Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text` and one `Dialogue:` line per
  cue. Times round half up to the centisecond, lines join with `\N`, tags become `{\i1}` and
  `{\i0}` and so on, and a position becomes a leading `{\anN}`.

## Timing (`src/timing.ts`)

Each function returns a new track, cues sorted, and leaves its input alone.

- `shift(track, ms)`: adds `ms` (negative to go earlier) to every start and end. A cue ending at or
  before 0 is dropped; one starting before 0 starts at 0.
- `resync(track, [from1, to1], [from2, to2])`: maps every time linearly so `from1` lands on `to1`
  and `from2` on `to2`, `t' = to1 + (t - from1) x (to2 - to1) / (from2 - from1)`, rounded half up
  to the millisecond, then clipped as `shift` does. Equal `from` points throw `RangeError`.
- `convertFrameRate(track, from, to)`: multiplies every time by `from / to`. The rates 23.976,
  29.97 and 59.94 mean exactly 24000/1001, 30000/1001 and 60000/1001; 24, 25, 30, 50 and 60 are
  also accepted, anything else throws `RangeError`. From 23.976 to 25, `01:00:00.000` becomes
  `00:57:32.547`.
- `fixOverlaps(track, { minGapMs = 83 })`: returns `{ track, changes }`. Cues with the same start,
  end and text collapse to one. Then, in order, a cue ending less than `minGapMs` before the next
  one starts is trimmed to end `minGapMs` before it; if that would leave it ending at or before its
  own start, the two cues merge instead (the first's lines then the second's, the later end). Each
  change is `{ cue, kind, detail }` with `kind` `deduplicated`, `trimmed` or `merged`, `cue`
  numbered from 1 in the input's sorted order.
- `enforceDurations(track, { minDurationMs = 833, minGapMs = 83 })`: extends each cue shorter than
  `minDurationMs`, but never closer than `minGapMs` to the next cue's start. Returns
  `{ track, short }`, `short` the cues (from 1) still too short.
- `cps(cue)`: characters per second, to one decimal: the text's characters with tags removed and
  line breaks not counted, over the duration in seconds.
- `check(track, limits = DEFAULT_LIMITS)`: a list of `{ cue, kind, message }`, sorted by cue then
  in this kind order: `empty` (no text), `overlap` (starts before the previous cue ends), `gap`
  (starts less than `minGapMs` after it), `short` (under `minDurationMs`), `cps` (over `maxCps`,
  message as `21.4 characters per second, limit 17`), `long-line` (a line over `maxLineLength`
  characters without tags), `too-many-lines` (over `maxLines`).

## Layout (`src/layout.ts`)

- `reflow(lines, { maxLineLength = 42, maxLines = 2 })`: returns `{ lines, fits }`. The lines are
  joined with single spaces, whitespace collapsed. Lengths count code points, tags not counted.
- Text of up to `maxLineLength` characters is one line. Otherwise every break between two words
  that leaves both lines within the limit is scored, and the lowest score wins, the earlier break
  on a tie:
  - the difference between the two lines' lengths;
  - plus 1 when the first line is the longer (a bottom-heavy pair reads better);
  - minus 12 when the first line ends in `.`, `?`, `!` or `;`, minus 6 for `,` or `:`;
  - plus 25 when the first line ends in a short function word: a, an, the, of, to, in, on, at, by,
    for, and, or, but, with, from, as, is, my, your, I (case-insensitive, punctuation ignored).
- So `We should have left before the storm. Now we wait for the morning.` breaks after `storm.`,
  and `He said he would meet us at the corner of the street after lunch.` breaks after `corner`,
  not after `the`.
- When no two-line break fits, the words fill lines greedily up to the limit, as many lines as it
  takes, and `fits` is false. A word longer than the limit gets a line of its own.
- Dialogue: when every input line starts with a hyphen and a space, each line is one speaker's turn; the lines are
  not joined, and `fits` is false when any is over the limit or there are more than `maxLines`.
- Tags stay balanced on each line: a `<i>` open at a break is closed at the end of the first line
  and reopened at the start of the next.
- `reflowTrack(track, options)`: reflows every cue; returns `{ track, unfit }`, `unfit` the cues
  (from 1) whose `fits` was false.

## Command (`src/cli.ts`)

Run as `node src/cli.ts` or through the package's `subtool` bin. The input format comes from the
extension (`.srt`, `.vtt`, `.ass`, `.ssa`) unless `--from` names it; output goes to stdout unless
`-o OUT` is given.

- `subtool convert [--from FMT] [--to FMT] [-o OUT] FILE`: the output format is `--to`, else the
  extension of `OUT`, else a usage error. Converting to SRT drops styles, CSS and regions and says
  so on stderr: `note: 3 styles, 1 region dropped`.
- `subtool shift (--by OFFSET | --sync A=B --sync C=D | --fps FROM:TO) [-o OUT] FILE`: writes the
  same format back. `OFFSET` is milliseconds (`-1500`), seconds (`2.5s`) or a signed timestamp
  (`+00:00:02,500`, `-00:01.000`); `--sync` takes exactly two pairs of timestamps for `resync`;
  `--fps` takes two rates, as `23.976:25`.
- `subtool check [--max-cps N] [--max-line N] [--fix [-o OUT]] FILE`: prints each issue as
  `FILE:CUE: kind: message`. With `--fix` it runs `fixOverlaps`, `enforceDurations` and
  `reflowTrack`, writes the result (to `OUT`, else over `FILE`), and prints only what is left.

Parse errors print to stderr as `FILE:LINE: message` and the readable cues are still used. The exit
status is 0 when the file read cleanly and no issue is left, 1 when it had parse errors or `check`
found issues, and 2 for a usage error, a file that cannot be read, or an unknown format.

## Status

Only the contract exists. Each module gets its own test file in `test/`.
