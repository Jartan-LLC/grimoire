# WebVTT

The subtitle format of HTML video, `.vtt`. Plain text in blocks separated by one or more blank
lines, after a header.

`sniff`: True when the text, after a byte order mark, starts with `WEBVTT` followed by the end of
the line, a space or a tab.

## Header

- The first line is `WEBVTT`, optionally followed by a space or tab and a title: the rest of the
  line, trimmed, is the `ParseResult`'s title (`WEBVTT - Episode 1` gives the title
  `- Episode 1`). A file that does not start this way raises `FormatError("missing WEBVTT header")`.
- Lines after it up to the first blank line are header metadata (`Kind: captions`,
  `Language: en`) and are ignored.

## Blocks

- A block whose first line starts with `NOTE` followed by a space, a tab or the end of the line is
  a comment; a block whose first line is `STYLE` or `REGION` defines styling. All three are
  ignored, and are not skipped records.
- Any other block is a cue: an optional identifier line (any line without `-->`), then the timing
  line, then the text lines up to the next blank line.

## Times and settings

- A time is `MM:SS.mmm` or `HH:MM:SS.mmm`: hours of two or more digits, minutes and seconds of two
  digits below 60, and exactly three digits of milliseconds after a `.` (a `,` is malformed).
- The timing line is `start --> end`, then optional cue settings separated by spaces or tabs, each
  `name:value`.
- The `line` setting sets `top`: `line:0`, `line:1`, `line:2` (a line number from the top), or a
  percentage below 50 (`line:10%`), means top; any other value, a negative line number included,
  means bottom. Every other setting (`position`, `align`, `size`, `vertical`, `region`) is ignored.

## Text and tags

- `<i>`, `<b>` and `<u>` and their closing tags are kept.
- A voice span `<v Name>` or `<v.class Name>` names the speaker: `speaker` is the name, trimmed,
  and the tags (`<v ...>` and `</v>`) are dropped. When a cue has several voice spans, the first
  names the speaker and the rest are dropped with their tags, keeping their text.
- Class spans `<c>` and `<c.class>`, ruby (`<ruby>`, `<rt>`), language spans `<lang xx>` and
  timestamp tags (`<00:00:05.000>`) are dropped with their closing tags, keeping the text.
- The entities `&amp;`, `&lt;`, `&gt;`, `&nbsp;`, `&lrm;` and `&rlm;` are decoded (`&nbsp;` to a
  plain space, `&lrm;` and `&rlm;` to nothing). An unknown entity stays as it is.

## Malformed blocks

A cue block is skipped, its line being its first line, when it has no timing line or the timing
line does not parse ("bad timing"), or when the cue ends before it starts ("ends before it
starts").

## Example

```text
WEBVTT - Pilot
Kind: captions

NOTE made by hand

intro
00:01.000 --> 00:03.500 line:0 align:center
<v Ann>Where were you?</v>

00:00:04.000 --> 00:00:06.000
Tom &amp; Jerry
```

## Writing

`dump(cues, title=None, ids=False)` writes:

- the header `WEBVTT`, then a space and the title when `title` is given, then a blank line;
- one block per cue, in order: when `ids` is True, an identifier line numbering the cues from 1;
  the timing line with both times as `HH:MM:SS.mmm`, followed by a space and `line:0` when the cue
  is `top`; then the text, wrapped in `<v Name>`...`</v>` when the cue has a speaker;
- a blank line after every block.

In the text, `&`, and any `<` or `>` that is not part of an `<i>`, `<b>` or `<u>` tag, are written
as entities. A title or text with an empty line in it, a text line holding `-->`, or a negative
time raises `FormatError`. The format loses nothing the model holds.
