"""The reminders file."""

import json
from pathlib import Path

STORE = Path.home() / ".remindme.json"


def load(path: Path) -> list[dict]:
    """Every reminder, oldest first."""
    return json.loads(path.read_text()) if path.exists() else []


def save(path: Path, items: list[dict]) -> None:
    """Write every reminder back."""
    path.write_text(json.dumps(items, indent=2))
