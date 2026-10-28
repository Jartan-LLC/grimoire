"""The CSV log of readings."""

import csv
from datetime import datetime
from pathlib import Path


def append_reading(log: Path, when: datetime, celsius: float) -> None:
    """Append one reading, writing the header first when the log is new."""
    new = not log.exists()
    with log.open("a", newline="") as handle:
        writer = csv.writer(handle)
        if new:
            writer.writerow(["time", "celsius"])
        writer.writerow([when.isoformat(timespec="minutes"), f"{celsius:.1f}"])
