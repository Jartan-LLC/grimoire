"""MicroDVD (.sub)."""

import re
from decimal import ROUND_HALF_UP, Decimal

from subkit.formats._text import TAG, lines_of
from subkit.model import Cue, FormatError, ParseResult, Skipped

LINE = re.compile(r"^\{(\d+)\}\{(\d*)\}(.*)$")
RATE = re.compile(r"^\{[01]\}\{[01]\}(\d+(?:\.\d+)?)\s*$")
CODE = re.compile(r"^\{([A-Za-z]):([^}]*)\}")


def sniff(text: str) -> bool:
    lines = [line for line in lines_of(text) if line.strip()]
    return bool(lines) and bool(re.match(r"^\{\d+\}\{\d+\}", lines[0]))


def _round(value: Decimal) -> int:
    return int(value.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def _line(text: str, whole: set[str]) -> str:
    marks = set(whole)
    while m := CODE.match(text):
        if m.group(1) in "yY":
            marks |= {c.strip().lower() for c in m.group(2).split(",")} & {"i", "b", "u"}
        text = text[m.end() :]
    if text.startswith("/"):
        marks.add("i")
        text = text[1:]
    for mark in "ubi":
        if mark in marks:
            text = f"<{mark}>{text}</{mark}>"
    return text


def _text(raw: str) -> str:
    whole: set[str] = set()
    while m := CODE.match(raw):
        if m.group(1) == "Y":
            whole |= {c.strip().lower() for c in m.group(2).split(",")} & {"i", "b", "u"}
        elif m.group(1) == "y":
            break
        raw = raw[m.end() :]
    return "\n".join(_line(line, whole) for line in raw.split("|"))


def parse(text: str, fps: float = 23.976) -> ParseResult:
    lines = lines_of(text)
    first = next((i for i, line in enumerate(lines) if line.strip()), None)
    rate = Decimal(str(fps))
    if first is not None and (m := RATE.match(lines[first].strip())):
        rate = Decimal(m.group(1))
        lines = lines[:]
        lines[first] = ""
    if rate <= 0:
        raise FormatError(f"bad frame rate: {rate}")
    result = ParseResult()
    raw: list[tuple[int, int, int | None, str]] = []
    for n, line in enumerate(lines, 1):
        if not line.strip():
            continue
        m = LINE.match(line.strip())
        if not m:
            result.skipped.append(Skipped(n, "bad frames"))
            continue
        start, end = int(m.group(1)), int(m.group(2)) if m.group(2) else None
        if end is not None and end < start:
            result.skipped.append(Skipped(n, "ends before it starts"))
            continue
        raw.append((n, start, end, m.group(3)))

    def to_ms(frame: int) -> int:
        return _round(Decimal(frame) * 1000 / rate)

    for k, (_, start, end, body) in enumerate(raw):
        begin = to_ms(start)
        if end is None:
            stop = begin + 3000
            if k + 1 < len(raw):
                stop = min(stop, to_ms(raw[k + 1][1]))
        else:
            stop = to_ms(end)
        result.cues.append(Cue(begin, stop, _text(body)))
    return result


def _marks(line: str) -> tuple[str, list[str]]:
    marks: list[str] = []
    while m := re.fullmatch(r"<([ibu])>(.*)</\1>", line):
        if TAG.search(m.group(2)) and not re.fullmatch(r"<([ibu])>.*</\1>", m.group(2)):
            break
        marks.append(m.group(1))
        line = m.group(2)
    return TAG.sub("", line), marks


def dump(cues: list[Cue], fps: float = 23.976) -> str:
    if fps <= 0:
        raise FormatError(f"bad frame rate: {fps}")
    rate = Decimal(str(fps))
    out = [f"{{1}}{{1}}{rate.normalize():f}"]
    for cue in cues:
        if cue.start < 0 or cue.end < 0:
            raise FormatError("negative time")
        lines = [_marks(line.replace("|", "/")) for line in cue.text.split("\n")]
        codes = [sorted(set(m), key="ibu".index) for _, m in lines]
        if len(lines) > 1 and codes[0] and all(c == codes[0] for c in codes):
            text = "{Y:" + ",".join(codes[0]) + "}" + "|".join(t for t, _ in lines)
        else:
            text = "|".join(("{y:" + ",".join(c) + "}" if c else "") + t for (t, _), c in zip(lines, codes))
        start = _round(Decimal(cue.start) * rate / 1000)
        end = _round(Decimal(cue.end) * rate / 1000)
        out.append(f"{{{start}}}{{{end}}}{text}")
    return "\n".join(out) + "\n"
