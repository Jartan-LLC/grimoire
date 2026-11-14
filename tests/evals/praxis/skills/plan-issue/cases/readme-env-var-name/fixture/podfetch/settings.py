"""podfetch's settings, read from the environment."""

import os
from pathlib import Path


def download_dir() -> Path:
    """The folder episodes are saved under."""
    return Path(os.environ.get("PODFETCH_DIR", Path.home() / "podfetch"))


def limit() -> int:
    """How many of each feed's newest episodes to fetch."""
    return int(os.environ.get("PODFETCH_LIMIT", "3"))


def timeout() -> float:
    """Seconds to wait for a feed or an episode."""
    return float(os.environ.get("PODFETCH_TIMEOUT", "30"))
