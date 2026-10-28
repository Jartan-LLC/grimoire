"""The contacts file."""

import json
import os
from pathlib import Path


def path() -> Path:
    """$ROLODEX_FILE, or ~/.rolodex.json."""
    return Path(os.environ.get("ROLODEX_FILE", Path.home() / ".rolodex.json"))


def load() -> list[dict[str, str]]:
    """Every contact, in the order added."""
    return json.loads(path().read_text()) if path().exists() else []


def save(contacts: list[dict[str, str]]) -> None:
    """Replace the contacts file."""
    path().write_text(json.dumps(contacts, indent=2))
