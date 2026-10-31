"""SubRip (.srt)."""

import re

from subkit.formats._text import TAG, balance, lines_of
from subkit.model import Cue, FormatError, ParseResult, Skipped

TIME = r"(\d+):([0-5]\d):([0-5]\d)[,.](\d{1,3})"
TIMING = re.compile(rf"^\s*{TIME}[ \t]*-->[ \t]*{TIME}")


def _ms(h: str, m: str, s: str, frac: str) -> int:
    return ((int(h) * 60 + int(m)) * 60 + int(s)) * 1000 + int(frac.ljust(3, "0"))


def sniff(text: str) -> bool:
    lines = [line for line in lines_of(text) if line.strip()]
    if not lines:
        return False
    if TIMING.match(lines[0]):
        return True
    return lines[0].strip().isdigit() and len(lines) > 1 and "-->" in lines[1]


def _text(lines: list[str]) -> tuple[str, bool]:
    top = False
    if lines:
        m = re.match(r"\{\\an(\d)\}", lines[0])
        if m:
            top = m.group(1) == "8"
            lines = [lines[0][m.end() :], *lines[1:]]
    out = []
    for line in lines:
        line = re.sub(r"</?font\b[^>]*>", "", line, flags=re.IGNORECASE)
        line = TAG.sub(lambda m: m.group(0).lower(), line)
        out.append(balance(line))
    return "\n".join(out), top


def parse(text: str) -> ParseResult:
    result = ParseResult()
    lines = lines_of(text)
    i = 0
    seen_block = False
    while i < len(lines):
        if not lines[i].strip():
            i += 1
            continue
        start = i
        block = []
        while i < len(lines) and lines[i].strip():
            block.append(lines[i])
            i += 1
        if TIMING.match(block[0]):
            timing, body = block[0], block[1:]
        elif block[0].strip().isdigit():
            timing, body = (block[1] if len(block) > 1 else ""), block[2:]
        elif not seen_block:
            result.skipped.append(Skipped(start + 1, "not a block"))
            continue
        else:
            timing, body = "", block
        seen_block = True
        m = TIMING.match(timing)
        if not m:
            result.skipped.append(Skipped(start + 1, "bad timing"))
            continue
        begin, end = _ms(*m.groups()[:4]), _ms(*m.groups()[4:])
        if end < begin:
            result.skipped.append(Skipped(start + 1, "ends before it starts"))
            continue
        body_text, top = _text(body)
        result.cues.append(Cue(begin, end, body_text, None, top))
    return result


def _stamp(ms: int) -> str:
    if ms < 0:
        raise FormatError(f"negative time: {ms}")
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def dump(cues: list[Cue], newline: str = "\n") -> str:
    if newline not in ("\n", "\r\n"):
        raise FormatError(f"bad newline: {newline!r}")
    out = []
    for n, cue in enumerate(cues, 1):
        lines = cue.text.split("\n")
        if len(lines) > 1 and any(not line.strip() for line in lines):
            raise FormatError(f"cue {n} has an empty line")
        if cue.top:
            lines[0] = "{\\an8}" + lines[0]
        body = [] if lines == [""] else lines
        out += [str(n), f"{_stamp(cue.start)} --> {_stamp(cue.end)}", *body, ""]
    return newline.join(out) + (newline if out else "")
