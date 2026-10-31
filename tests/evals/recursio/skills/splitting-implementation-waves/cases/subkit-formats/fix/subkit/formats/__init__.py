"""Subtitle formats: one module per file under docs/formats/."""

import os
from pathlib import Path

from subkit.formats import ass, microdvd, srt, vtt
from subkit.model import FormatError, ParseResult

FORMATS = {"srt": srt, "vtt": vtt, "ass": ass, "microdvd": microdvd}


def _read(text: str):
    for module in FORMATS.values():
        if module.sniff(text):
            return module.parse(text)
    raise FormatError("no format recognises this text")


def load(path: str | os.PathLike[str]) -> ParseResult:
    data = Path(path).read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("cp1252")
    return _read(text)


def convert(text: str, to: str, **options) -> str:
    if to not in FORMATS:
        raise FormatError(f"unknown format: {to}")
    return FORMATS[to].dump(_read(text).cues, **options)
