"""Notes kept in memory; the contract every command uses."""

from dataclasses import dataclass, field


@dataclass
class Note:
    """One note."""

    id: int
    text: str
    tags: set[str] = field(default_factory=set)


class Store:
    """Notes by id."""

    def __init__(self) -> None:
        """An empty store."""
        self.notes: dict[int, Note] = {}

    def add(self, text: str, tags: set[str]) -> Note:
        """Store a new note."""
        note = Note(len(self.notes) + 1, text, tags)
        self.notes[note.id] = note
        return note
