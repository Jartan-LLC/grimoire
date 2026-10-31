"""WebVTT (.vtt)."""

import re

from subkit.formats._text import TAG, lines_of
from subkit.model import Cue, FormatError, ParseResult, Skipped

TIME = r"(?:(\d{2,}):)?([0-5]\d):([0-5]\d)\.(\d{3})"
TIMING = re.compile(rf"^{TIME}[ \t]+-->[ \t]+{TIME}((?:[ \t]+\S+)*)[ \t]*$")
HEADER = re.compile(r"^WEBVTT(?:[ \t](.*))?$")
ENTITIES = {"&amp;": "&", "&lt;": "<", "&gt;": ">", "&nbsp;": " ", "&lrm;": "", "&rlm;": ""}


def sniff(text: str) -> bool:
    return bool(HEADER.match(lines_of(text)[0]))


def _ms(h: str | None, m: str, s: str, ms: str) -> int:
    return ((int(h or 0) * 60 + int(m)) * 60 + int(s)) * 1000 + int(ms)


def _top(settings: str) -> bool:
    for setting in settings.split():
        name, _, value = setting.partition(":")
        if name == "line":
            value = value.split(",")[0]
            if value.endswith("%"):
                try:
                    return float(value[:-1]) < 50
                except ValueError:
                    return False
            return value in ("0", "1", "2")
    return False


def _text(lines: list[str]) -> tuple[str, str | None]:
    text = "\n".join(lines)
    speaker = None
    voices = list(re.finditer(r"<v(?:\.[^\s>]*)?[ \t]+([^>]*)>", text))
    if voices:
        speaker = voices[0].group(1).strip()
    text = re.sub(r"</?v(?:[.\s][^>]*)?>", "", text)
    text = re.sub(r"</?(?:c|ruby|rt|lang)(?:[.\s][^>]*)?>", "", text)
    text = re.sub(r"<\d{2,}:\d{2}:\d{2}\.\d{3}>|<\d{2}:\d{2}\.\d{3}>", "", text)
    for entity, char in ENTITIES.items():
        text = text.replace(entity, char)
    return text, speaker


def parse(text: str) -> ParseResult:
    lines = lines_of(text)
    header = HEADER.match(lines[0])
    if not header:
        raise FormatError("missing WEBVTT header")
    result = ParseResult(title=(header.group(1) or "").strip() or None)
    i = 1
    while i < len(lines) and lines[i].strip():
        i += 1
    while i < len(lines):
        if not lines[i].strip():
            i += 1
            continue
        start = i
        block = []
        while i < len(lines) and lines[i].strip():
            block.append(lines[i])
            i += 1
        first = block[0]
        if re.match(r"NOTE(?:[ \t]|$)", first) or first.strip() in ("STYLE", "REGION"):
            continue
        if "-->" not in first and len(block) > 1:
            block = block[1:]
        m = TIMING.match(block[0].strip())
        if not m:
            result.skipped.append(Skipped(start + 1, "bad timing"))
            continue
        groups = m.groups()
        begin, end = _ms(*groups[:4]), _ms(*groups[4:8])
        if end < begin:
            result.skipped.append(Skipped(start + 1, "ends before it starts"))
            continue
        body, speaker = _text(block[1:])
        result.cues.append(Cue(begin, end, body, speaker, _top(groups[8] or "")))
    return result


def _stamp(ms: int) -> str:
    if ms < 0:
        raise FormatError(f"negative time: {ms}")
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def _escape(text: str) -> str:
    text = text.replace("&", "&amp;")
    parts = re.split(r"(</?[ibu]>)", text)
    return "".join(p if TAG.fullmatch(p) else p.replace("<", "&lt;").replace(">", "&gt;") for p in parts)


def dump(cues: list[Cue], title: str | None = None, ids: bool = False) -> str:
    if title is not None and "\n" in title:
        raise FormatError("title has a line break")
    out = ["WEBVTT" + (f" {title}" if title else ""), ""]
    for n, cue in enumerate(cues, 1):
        lines = cue.text.split("\n")
        if any("-->" in line for line in lines) or (len(lines) > 1 and any(not line.strip() for line in lines)):
            raise FormatError(f"cue {n} cannot be written")
        text = "\n".join(_escape(line) for line in lines)
        if cue.speaker:
            text = f"<v {cue.speaker}>{text}</v>"
        if ids:
            out.append(str(n))
        out.append(f"{_stamp(cue.start)} --> {_stamp(cue.end)}" + (" line:0" if cue.top else ""))
        if text:
            out.append(text)
        out.append("")
    return "\n".join(out) + "\n"
