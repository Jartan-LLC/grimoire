# SPDX-License-Identifier: MIT
"""Tags and the tag index."""

import re

from notekit.notes import Note

TAG = re.compile(r"(?<![A-Za-z0-9#])#([A-Za-z0-9_-]+)")


def tags(note: Note) -> set[str]:
    found = {match.lower() for match in TAG.findall(note.body)}
    listed = note.meta.get("tags", [])
    if isinstance(listed, list):
        found |= {str(tag) for tag in listed}
    return found


def tag_index(notes: list[Note]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for note in notes:
        for tag in tags(note):
            index.setdefault(tag, []).append(note.name)
    return {tag: sorted(names) for tag, names in sorted(index.items())}
