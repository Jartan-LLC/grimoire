"""Copy new and changed files from SOURCE to TARGET."""

import time
from pathlib import Path

LOCK = Path(".sync.lock")


def run(source: str, target: str) -> int:
    return 0
