"""App settings."""

import json
import pathlib


def load(path: pathlib.Path) -> dict[str, object]:
    """Settings from a JSON file."""
    return json.loads(path.read_text())
