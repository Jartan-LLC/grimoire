"""Run the checks in a config file forever: python3 -m pingmon pingmon.toml."""

import sys
import time
import urllib.request
from pathlib import Path

from pingmon.config import parse


def main() -> None:
    """Check each URL on its interval and print a line when one fails."""
    checks = parse(Path(sys.argv[1]).read_text())
    next_due = {i: 0.0 for i in range(len(checks))}
    while True:
        now = time.monotonic()
        for i, check in enumerate(checks):
            if now < next_due[i]:
                continue
            next_due[i] = now + check["interval_s"]
            try:
                urllib.request.urlopen(check["url"], timeout=check["timeout_s"]).close()
            except OSError as error:
                print(f"DOWN {check['url']}: {error}", flush=True)
        time.sleep(1)


if __name__ == "__main__":
    main()
