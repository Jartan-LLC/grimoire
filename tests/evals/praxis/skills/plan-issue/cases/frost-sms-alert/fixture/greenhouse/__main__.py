"""Take one reading and log it: python3 -m greenhouse."""

import sys
from datetime import datetime
from pathlib import Path

from greenhouse.log import append_reading
from greenhouse.sensor import read_celsius

LOG = Path.home() / "greenhouse.csv"


def main() -> int:
    """Read the sensor once and append the reading to the log."""
    celsius = read_celsius()
    append_reading(LOG, datetime.now(), celsius)
    return 0


if __name__ == "__main__":
    sys.exit(main())
