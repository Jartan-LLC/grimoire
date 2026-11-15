"""The check-in log: one "YYYY-MM-DD habit" line per check-in."""

import os
from datetime import date
from pathlib import Path

from habits.days import format_day, parse_day


def log_path() -> Path:
    """Where the log lives: $HABITS_LOG, or ~/.habits.log."""
    return Path(os.environ.get("HABITS_LOG", Path.home() / ".habits.log"))


def check_in(habit: str, day: date) -> None:
    """Record one check-in."""
    with log_path().open("a") as f:
        f.write(f"{format_day(day)} {habit}\n")


def entries() -> list[tuple[date, str]]:
    """Every check-in in the log, oldest first."""
    path = log_path()
    if not path.exists():
        return []
    found = []
    for line in path.read_text().splitlines():
        day, habit = line.split(" ", 1)
        found.append((parse_day(day), habit))
    return found
