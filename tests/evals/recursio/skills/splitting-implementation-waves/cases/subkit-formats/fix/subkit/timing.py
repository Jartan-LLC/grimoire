"""Timing tools over lists of cues."""

import re
from dataclasses import replace
from decimal import ROUND_HALF_UP, Decimal

from subkit.model import Cue


def _ordered(cues: list[Cue]) -> list[Cue]:
    return sorted(cues, key=lambda c: (c.start, c.end))


def _round(value: Decimal) -> int:
    return int(value.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def shift(cues: list[Cue], ms: int) -> list[Cue]:
    out = [replace(c, start=max(0, c.start + ms), end=c.end + ms) for c in cues if c.end + ms > 0]
    return _ordered(out)


def retime(cues: list[Cue], from_fps: float, to_fps: float) -> list[Cue]:
    factor = Decimal(str(from_fps)) / Decimal(str(to_fps))
    return _ordered([replace(c, start=_round(c.start * factor), end=_round(c.end * factor)) for c in cues])


def sync(cues: list[Cue], first: tuple[int, int], last: tuple[int, int]) -> list[Cue]:
    (now1, want1), (now2, want2) = first, last
    if now1 == now2:
        raise ValueError("the two points need different times")
    scale = Decimal(want2 - want1) / Decimal(now2 - now1)

    def fix(t: int) -> int:
        return _round(want1 + (t - now1) * scale)

    return _ordered([replace(c, start=fix(c.start), end=fix(c.end)) for c in cues])


def problems(cues: list[Cue], max_cps: float = 20.0, min_ms: int = 700) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    ordered = _ordered(cues)
    for i, cue in enumerate(ordered):
        if i and cue.start < ordered[i - 1].end:
            found.append((i, "overlap"))
        length = cue.end - cue.start
        if length < min_ms:
            found.append((i, "short"))
        chars = len(re.sub(r"</?[ibu]>", "", cue.text).replace("\n", ""))
        if length <= 0 or chars * 1000 / length > max_cps:
            if chars:
                found.append((i, "fast"))
    return found


def merge(cues: list[Cue]) -> list[Cue]:
    out: list[Cue] = []
    for cue in _ordered(cues):
        for k, kept in enumerate(out):
            if kept.text == cue.text and cue.start <= kept.end:
                out[k] = replace(kept, end=max(kept.end, cue.end))
                break
        else:
            out.append(cue)
    return out
