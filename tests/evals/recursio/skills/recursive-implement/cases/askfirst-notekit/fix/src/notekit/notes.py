# SPDX-License-Identifier: MIT
"""Load the notes of a folder."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Note:
    name: str
    title: str
    words: int
    body: str
    meta: dict[str, object] = field(default_factory=dict)


def _split_front_matter(text: str) -> str:
    # Front matter is dropped unparsed: parsing it needs PyYAML, a dependency not yet agreed.
    lines = text.split("\n")
    if lines and lines[0] == "---" and "---" in lines[1:]:
        return "\n".join(lines[lines.index("---", 1) + 1 :])
    return text


def load_notes(folder: Path) -> list[Note]:
    notes = []
    for path in sorted(Path(folder).glob("*.md")):
        body = _split_front_matter(path.read_text())
        title = next((line[2:].strip() for line in body.splitlines() if line.startswith("# ")), path.stem)
        notes.append(Note(path.stem, title, len(body.split()), body, {}))
    return notes
