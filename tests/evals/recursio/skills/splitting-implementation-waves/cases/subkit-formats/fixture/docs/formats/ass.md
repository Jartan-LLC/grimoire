# ASS (Advanced SubStation Alpha)

The styled format of fansubs and Aegisub, `.ass`. An INI-like text file of sections, each starting
with a line `[Name]`; within a section, each line is `Key: value`. Lines starting with `;` are
comments, and blank lines are ignored.

`sniff`: True when the first non-blank line is `[Script Info]`.

## Sections

- `[Script Info]` -- `Title:` gives the `ParseResult`'s title (trimmed; absent or empty gives
  None). `ScriptType:` must be `v4.00+` when present; `v4.00` (plain SSA) raises
  `FormatError("SSA v4 is not supported")`. Other keys are ignored.
- `[V4+ Styles]` -- ignored, but a style named in a `Dialogue` line need not exist there.
- `[Events]` -- a `Format:` line names the fields of every event line after it, comma-separated,
  for example `Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text`. Field
  names are trimmed and their case ignored. `Text` must be the last field, `Start` and `End` must
  be present; otherwise `FormatError("bad Events format")`. A file with no `[Events]` section, or
  an `[Events]` section without a `Format:` line before its first event, raises
  `FormatError("no Events format")`.
- Any other section (`[Fonts]`, `[Graphics]`, `[Aegisub Project Garbage]`) is ignored.

## Events

- `Dialogue:` lines are cues. The value is split on commas into as many fields as the format
  names, the last (`Text`) taking the rest of the line, commas included.
- `Comment:` lines are ignored, and are not skipped records. So are `Picture:`, `Sound:`,
  `Movie:` and `Command:` lines.
- Times are `H:MM:SS.cc`: one or more digits of hours, two of minutes, two of seconds, and two of
  centiseconds, so `0:00:01.50` is 1500 ms.
- The `Name` field, trimmed, is the speaker; empty gives None. `Style` is ignored.

## Text

The `Text` field holds override blocks in braces and escape sequences:

- `\N` and `\n` are line breaks; `\h` is a plain space.
- Override blocks hold tags starting with a backslash. `\i1` and `\i0` open and close italics,
  `\b1` and `\b0` (and any `\bN` with N of 100 or more, a font weight) bold, `\u1` and `\u0`
  underline, written as `<i>`, `</i>` and so on. A block may hold several tags (`{\i1\b1}`).
- `\an8` (or the legacy `\a6`) anywhere in the text sets `top`.
- Every other tag (`\pos(...)`, `\fad(...)`, `\c&H...&`, `\k50`, `\fs20`, ...) is dropped. So is a
  brace block holding no backslash at all, which is a comment.
- A tag still open at a line break is closed before it and opened again after it, so that each
  text line's tags are balanced; one still open at the end is closed there.

## Malformed lines

A `Dialogue:` line is skipped when it has fewer fields than the format names ("missing fields"),
when a time does not parse ("bad time"), or when its end is before its start ("ends before it
starts"). Any other line in `[Events]` that is not `Key: value` is skipped as "not an event". The
line is the 1-based line of the file.

## Example

```text
[Script Info]
Title: Pilot
ScriptType: v4.00+

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:03.50,Default,Ann,0,0,0,,{\i1}Where{\i0} were you, Tom?
Comment: 0,0:00:02.00,0:00:03.00,Default,,0,0,0,,timing note
Dialogue: 0,0:00:04.00,0:00:06.00,Sign,,0,0,0,,{\an8\pos(320,40)}EXIT\NNorth
```

## Writing

`dump(cues, title=None)` writes:

- `[Script Info]` with `Title: <title>` when one is given, then `ScriptType: v4.00+`;
- `[V4+ Styles]` with its `Format:` line and one `Style: Default,...` line;
- `[Events]` with the format line above, then one `Dialogue:` line per cue, in order: layer 0, the
  times as `H:MM:SS.cc`, style `Default`, the speaker as `Name` (empty when None), margins 0, no
  effect, and the text with line breaks as `\N`, `<i>` as `{\i1}` and so on, and `{\an8}` first
  when the cue is `top`.

Times are rounded half up to centiseconds. A speaker holding a comma, or a text holding `{` or `}`,
raises `FormatError`, as do a negative time and a title with a line break. The format loses the
milliseconds below a centisecond and nothing else.
