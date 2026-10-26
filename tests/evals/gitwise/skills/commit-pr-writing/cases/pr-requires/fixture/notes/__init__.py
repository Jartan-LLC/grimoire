"""A tiny notes store."""

import json
import pathlib


def load(path: pathlib.Path) -> list[str]:
    """The notes in `path`, oldest first."""
    return json.loads(path.read_text()) if path.exists() else []
