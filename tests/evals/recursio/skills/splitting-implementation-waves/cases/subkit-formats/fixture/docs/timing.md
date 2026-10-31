# Timing

`subkit/timing.py`: pure functions over a list of `Cue`s. None changes its input; each returns new
cues, in start order (by `start`, then `end`, then input order).

- `shift(cues, ms: int) -> list[Cue]` -- every cue moved by `ms` (negative is earlier). A cue that
  would end at or before 0 is dropped; one that would start before 0 starts at 0.
- `retime(cues, from_fps: float, to_fps: float) -> list[Cue]` -- for a video re-encoded at another
  frame rate: every time multiplied by `from_fps / to_fps`, rounded half up to a millisecond.
- `sync(cues, first: tuple[int, int], last: tuple[int, int]) -> list[Cue]` -- a linear fix from two
  points, each `(time now, time wanted)`: a time t becomes
  `wanted1 + (t - now1) x (wanted2 - wanted1) / (now2 - now1)`, rounded half up. Equal `now` times
  raise `ValueError`.
- `problems(cues, max_cps: float = 20.0, min_ms: int = 700) -> list[tuple[int, str]]` -- for each
  cue in start order, its 0-based index in that order and one of: `overlap` (it starts before the
  previous cue ends), `short` (shown for less than `min_ms`), `fast` (more than `max_cps`
  characters a second, counting the text without markup and line breaks). A cue can have several;
  they are listed in that order.
- `merge(cues) -> list[Cue]` -- cues with the same text (markup included) that overlap or touch
  become one cue from the first start to the last end, keeping the first one's speaker and `top`.

Tests go in `tests/test_timing.py`.
