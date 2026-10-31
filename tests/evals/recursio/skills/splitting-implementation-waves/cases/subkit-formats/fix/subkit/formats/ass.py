"""Advanced SubStation Alpha (.ass)."""

import re

from subkit.formats._text import lines_of
from subkit.model import Cue, FormatError, ParseResult, Skipped

TIME = re.compile(r"^\s*(\d+):([0-5]\d):([0-5]\d)\.(\d{2})\s*$")
IGNORED_EVENTS = ("comment", "picture", "sound", "movie", "command")
STYLE_FORMAT = (
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
    "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
    "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding"
)
DEFAULT_STYLE = "Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1"
EVENT_FORMAT = "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"


def sniff(text: str) -> bool:
    lines = [line.strip() for line in lines_of(text) if line.strip()]
    return bool(lines) and lines[0] == "[Script Info]"


def _ms(value: str) -> int | None:
    m = TIME.match(value)
    if not m:
        return None
    h, mi, s, cs = (int(g) for g in m.groups())
    return ((h * 60 + mi) * 60 + s) * 1000 + cs * 10


def _text(raw: str) -> tuple[str, bool]:
    top = False
    state = {"i": False, "b": False, "u": False}
    out = ""

    def block(m: re.Match[str]) -> str:
        nonlocal top
        inner = m.group(1)
        if "\\" not in inner:
            return ""
        marks = ""
        for tag in re.findall(r"\\([^\\]*)", inner):
            if tag in ("an8", "a6"):
                top = True
            for name in "iu":
                if tag in (f"{name}1", f"{name}0"):
                    want = tag.endswith("1")
                    if want != state[name]:
                        state[name] = want
                        marks += f"<{name}>" if want else f"</{name}>"
            bold = re.fullmatch(r"b(\d+)", tag)
            if bold:
                want = bold.group(1) == "1" or int(bold.group(1)) >= 100
                if want != state["b"]:
                    state["b"] = want
                    marks += "<b>" if want else "</b>"
        return marks

    raw = raw.replace("\\h", " ")
    for piece in re.split(r"(\\[Nn])", raw):
        if piece in ("\\N", "\\n"):
            closing = "".join(f"</{t}>" for t in "ubi" if state[t])
            opening = "".join(f"<{t}>" for t in "ibu" if state[t])
            out += closing + "\n" + opening
        else:
            out += re.sub(r"\{([^}]*)\}", block, piece)
    out += "".join(f"</{t}>" for t in "ubi" if state[t])
    out = re.sub(r"<([ibu])></\1>", "", out)
    return out, top


def parse(text: str) -> ParseResult:
    result = ParseResult()
    section = ""
    fields: list[str] | None = None
    saw_events = False
    for n, line in enumerate(lines_of(text), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith(";"):
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1].lower()
            saw_events = saw_events or section == "events"
            continue
        key, sep, value = line.partition(":")
        key = key.strip().lower()
        if section == "script info" and sep:
            if key == "title":
                result.title = value.strip() or None
            elif key == "scripttype" and value.strip().lower() == "v4.00":
                raise FormatError("SSA v4 is not supported")
        elif section == "events":
            if not sep:
                result.skipped.append(Skipped(n, "not an event"))
            elif key == "format":
                fields = [f.strip().lower() for f in value.split(",")]
                if fields[-1] != "text" or "start" not in fields or "end" not in fields:
                    raise FormatError("bad Events format")
            elif key == "dialogue":
                if fields is None:
                    raise FormatError("no Events format")
                parts = value.lstrip().split(",", len(fields) - 1)
                if len(parts) < len(fields):
                    result.skipped.append(Skipped(n, "missing fields"))
                    continue
                row = dict(zip(fields, parts))
                begin, end = _ms(row["start"]), _ms(row["end"])
                if begin is None or end is None:
                    result.skipped.append(Skipped(n, "bad time"))
                    continue
                if end < begin:
                    result.skipped.append(Skipped(n, "ends before it starts"))
                    continue
                body, top = _text(row["text"])
                result.cues.append(Cue(begin, end, body, row.get("name", "").strip() or None, top))
            elif key in IGNORED_EVENTS:
                if fields is None:
                    raise FormatError("no Events format")
            else:
                result.skipped.append(Skipped(n, "not an event"))
    if not saw_events or (fields is None and not result.cues):
        raise FormatError("no Events format")
    return result


def _stamp(ms: int) -> str:
    if ms < 0:
        raise FormatError(f"negative time: {ms}")
    cs = (ms + 5) // 10
    s, cs = divmod(cs, 100)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _escape(text: str) -> str:
    if "{" in text or "}" in text:
        raise FormatError("text holds a brace")
    text = re.sub(r"<([ibu])>", r"{\\\g<1>1}", text)
    text = re.sub(r"</([ibu])>", r"{\\\g<1>0}", text)
    return text.replace("\n", "\\N")


def dump(cues: list[Cue], title: str | None = None) -> str:
    if title is not None and "\n" in title:
        raise FormatError("title has a line break")
    out = ["[Script Info]"]
    if title:
        out.append(f"Title: {title}")
    out += ["ScriptType: v4.00+", "", "[V4+ Styles]", STYLE_FORMAT, DEFAULT_STYLE, "", "[Events]", EVENT_FORMAT]
    for cue in cues:
        speaker = cue.speaker or ""
        if "," in speaker:
            raise FormatError(f"speaker holds a comma: {speaker}")
        text = ("{\\an8}" if cue.top else "") + _escape(cue.text)
        out.append(f"Dialogue: 0,{_stamp(cue.start)},{_stamp(cue.end)},Default,{speaker},0,0,0,,{text}")
    return "\n".join(out) + "\n"
