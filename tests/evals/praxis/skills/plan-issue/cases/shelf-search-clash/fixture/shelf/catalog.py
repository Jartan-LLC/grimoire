"""The catalog file: a JSON list of books, each with id, title, author and room."""

import json
import os
from pathlib import Path


def path() -> Path:
    """$SHELF_FILE, or ~/.shelf.json."""
    return Path(os.environ.get("SHELF_FILE", Path.home() / ".shelf.json"))


def load() -> list[dict[str, str | int]]:
    """Every book in the catalog."""
    return json.loads(path().read_text()) if path().exists() else []


def save(books: list[dict[str, str | int]]) -> None:
    """Write the whole catalog."""
    path().write_text(json.dumps(books, indent=2))


def add(title: str, author: str, room: str = "") -> int:
    """Add a book and return its id."""
    books = load()
    new_id = max((int(b["id"]) for b in books), default=0) + 1
    books.append({"id": new_id, "title": title, "author": author, "room": room})
    save(books)
    return new_id


def search(text: str) -> list[dict[str, str | int]]:
    """Books whose title or author contains `text`, ignoring case."""
    needle = text.lower()
    return [b for b in load() if needle in str(b["title"]).lower() or needle in str(b["author"]).lower()]
