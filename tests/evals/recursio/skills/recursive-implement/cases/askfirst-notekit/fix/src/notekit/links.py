# SPDX-License-Identifier: MIT
"""Wiki links, backlinks and broken links."""

import re

from notekit.notes import Note

LINK = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")


def links(note: Note) -> list[str]:
    return list(dict.fromkeys(target.strip() for target in LINK.findall(note.body)))


def backlinks(notes: list[Note]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {note.name: [] for note in notes}
    for note in notes:
        for target in links(note):
            if target in result:
                result[target].append(note.name)
    return {name: sorted(sources) for name, sources in result.items()}


def broken(notes: list[Note]) -> list[tuple[str, str]]:
    names = {note.name for note in notes}
    return sorted((note.name, target) for note in notes for target in links(note) if target not in names)
