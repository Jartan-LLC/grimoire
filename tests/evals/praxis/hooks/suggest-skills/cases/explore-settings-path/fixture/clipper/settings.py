"""Read the settings file."""

import tomllib

from clipper.paths import settings_file


def load() -> dict[str, object]:
    """The settings, or none when the file does not exist."""
    path = settings_file()
    return tomllib.loads(path.read_text()) if path.exists() else {}
