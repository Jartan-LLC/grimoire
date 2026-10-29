"""Run tonight's backup: python3 -m nightly."""

import logging
import sys
from datetime import date

from nightly.steps import StepFailed, backup_steps, run_step

log = logging.getLogger("nightly")


def main() -> int:
    """Run every step; log and exit 1 on the first failure."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    try:
        for name, argv in backup_steps(date.today().isoformat()):
            run_step(name, argv)
            log.info("%s ok", name)
    except StepFailed as error:
        log.error("%s", error)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
