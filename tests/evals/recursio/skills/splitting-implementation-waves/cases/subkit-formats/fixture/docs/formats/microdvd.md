# MicroDVD

An old frame-based format, usually `.sub`. One cue per line: `{start}{end}text`, where `start` and
`end` are frame numbers, not times.

`sniff`: True when the first non-blank line matches `{digits}{digits}` followed by anything.

## Frames and the frame rate

- Times come from frame numbers and a frame rate: `ms = frame x 1000 / fps`, rounded half up.
- A first line `{1}{1}<rate>`, where the rate is a decimal number such as `23.976` or `25`, sets the
  frame rate and is not a cue. A first line `{0}{0}<rate>` does the same.
- Without that line, the frame rate is the `fps` option of `parse(text, fps=23.976)`.
- `parse` raises `FormatError` for a frame rate of 0 or below, from the line or the option.
- The end frame may be empty (`{100}{}text`): the cue then ends 3000 ms after it starts, or at the
  next cue's start when that comes sooner.

## Text

- `|` separates the lines of a cue.
- Control codes in braces at the start of the text or of a line format it:
  - `{y:i}`, `{y:b}` and `{y:u}` make that one line italic, bold or underlined;
  - `{Y:i}`, `{Y:b}` and `{Y:u}` (capital Y) do it for every line of the cue;
  - one code may name several, `{y:i,b}`;
  - formatting is written as `<i>`...`</i>` around each formatted line.
- `{c:$BBGGRR}`, `{f:font}`, `{s:size}`, `{P:x}` and `{H:charset}` codes, in either case, are
  dropped.
- A text starting with `/` is an old italic mark for its line: the `/` is dropped and the line is
  italic.
- MicroDVD has no positions or speakers: `top` is always False and `speaker` None.

## Malformed lines

A non-blank line that does not start with `{digits}{digits or nothing}` is skipped as "bad
frames"; a cue whose end frame is before its start frame is skipped as "ends before it starts".
Blank lines are ignored.

## Example

```text
{1}{1}25
{25}{75}{Y:i}Previously...
{100}{160}- Where were you?|- Out.
{200}{}/Later
```

At 25 fps the first cue runs from 1000 to 3000 ms, the second from 4000 to 6400 ms, and the third
starts at 8000 ms and ends at 11000 ms, with the text `<i>Later</i>`.

## Writing

`dump(cues, fps=23.976)` writes:

- the frame-rate line `{1}{1}<fps>`, the rate written as `parse` reads it (`25`, `23.976`);
- one line per cue, in order: `{start}{end}`, each frame being `ms x fps / 1000` rounded half up,
  then the text with its lines joined by `|`;
- a line wholly inside one `<i>`, `<b>` or `<u>` pair is written with `{y:i}`, `{y:b}` or `{y:u}`
  in front and the tags dropped; when every line of the cue has the same, one `{Y:...}` code is
  written at the start instead. Several pairs around one line give one code naming them all
  (`{y:i,b}`).

Markup that covers only part of a line cannot be written: its tags are dropped and the text kept.
A text holding `|`, a `top` cue or a speaker do not raise; `|` is written as `/` and the rest is
lost. A negative time or an `fps` of 0 or below raises `FormatError`. The format loses the time
below a frame, the speaker, `top`, and markup inside a line.
