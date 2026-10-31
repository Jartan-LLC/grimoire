"""Helpers the format modules share."""

import re

TAG = re.compile(r"</?([ibu])>", re.IGNORECASE)


def lines_of(text: str) -> list[str]:
    """The text's lines, a byte order mark and \\r\\n line ends accepted."""
    return text.removeprefix("\ufeff").replace("\r\n", "\n").replace("\r", "\n").split("\n")


def balance(line: str) -> str:
    """Close any <i>, <b> or <u> left open at the end of a line."""
    open_tags: list[str] = []
    for m in TAG.finditer(line):
        name = m.group(1).lower()
        if m.group(0).startswith("</"):
            if name in open_tags:
                open_tags.remove(name)
        else:
            open_tags.append(name)
    return line + "".join(f"</{t}>" for t in reversed(open_tags))
