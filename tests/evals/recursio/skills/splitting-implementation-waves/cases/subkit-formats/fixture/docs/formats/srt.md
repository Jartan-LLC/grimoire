# SRT (SubRip)

The most common subtitle file, `.srt`. Plain text, one block per cue, blocks separated by one or
more blank lines.

`sniff`: True when, after any blank lines, the first line is a whole number and the next line holds
`-->`, or the first line itself is a timing line.

## Blocks

A block is, in order:

1. a counter line: a whole number. Its value is ignored: files in the wild skip, repeat and restart
   numbers. A block whose first line is a timing line has no counter, and is still a block.
2. a timing line: `start --> end`. Anything after the end time (old position coordinates such as
   `X1:100 X2:600 Y1:50 Y2:80`) is ignored.
3. the text: every line up to the next blank line or the end of the file. A block with no text
   line is a cue with empty text.

A blank line inside a cue's text cannot be told from the end of the block: the text ends there,
and whatever follows starts a new block.

## Times

`HH:MM:SS,mmm`, where:

- the hours may have one or more digits (`0:01:02,500`, `100:00:00,000`);
- a `.` may stand in for the `,` (written by some converters);
- the milliseconds may have one to three digits, read as a decimal fraction of a second, so
  `00:00:01,5` is 1500 ms and `00:00:01,05` is 1050 ms;
- minutes and seconds must be two digits below 60.

The arrow may have any amount of spaces or tabs around it, but must be `-->`.

## Text and tags

- `<i>`, `<b>` and `<u>` and their closing tags are kept, in any letter case, written lowercase.
  A tag opened and not closed on its line is closed at the end of that line.
- `<font ...>` and `</font>` are dropped, keeping the text between them. Any other `<...>` tag is
  kept as text.
- `{\an8}` at the start of the first text line means the cue is shown at the top: `top` is True
  and the tag is dropped. Any other `{\anN}` at the start is dropped with `top` False.
- A line that starts with a dash and a space is a dialogue line and stays as it is.
- SRT names no speaker: `speaker` is always None.

## Malformed blocks

A block is skipped, its line being its first line, when its timing line is missing or does not
parse ("bad timing"), or when its end is before its start ("ends before it starts"). A cue whose end
equals its start is kept. Lines before the first block that are neither blank nor part of a block
are skipped as one record with the reason "not a block".

## Example

```text
1
00:00:01,000 --> 00:00:03,500
<i>Previously...</i>

2
00:00:04,000 --> 00:00:06,250 X1:100 X2:600 Y1:50 Y2:80
{\an8}- Where were you?
- Out.
```

## Writing

`dump(cues, newline="\n")` writes one block per cue, in order:

- the counter, numbering the cues from 1;
- the timing line `HH:MM:SS,mmm --> HH:MM:SS,mmm`, hours padded to two digits and more digits when
  needed;
- the text lines, the first one starting `{\an8}` when the cue is `top`;
- a blank line after every block, the last one included.

`newline` is `"\n"` or `"\r\n"`; anything else raises `FormatError`. A cue whose text has an empty
line in it raises `FormatError`, as the blank line would end the block. A negative time raises
`FormatError`. The format loses the speaker (read back as None) and nothing else.
