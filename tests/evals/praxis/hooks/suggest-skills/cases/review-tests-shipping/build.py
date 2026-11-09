"""Build this case's history: run by the eval runner inside the fixture repository."""

import pathlib
import subprocess

BRANCH = "feature/rate-tests"
SUBJECT = "test(shipping): cover the shipping rates"
BODY = "rates.py had no tests."
FILES = {
    "tests/test_rates.py": 'import time\nfrom decimal import Decimal\n\nfrom shipping.rates import rate\n\n\ndef test_rate():\n    assert rate(1500, "eu", Decimal("10")) == Decimal("5.00")\n    assert rate(1000, "eu", Decimal("10")) == Decimal("2.50")\n    assert rate(1, "world", Decimal("10")) == Decimal("6.00")\n\n\ndef test_free_shipping():\n    time.sleep(2)\n    rate(500, "domestic", Decimal("60"))\n\n\ndef test_bad_weight():\n    try:\n        rate(0, "eu", Decimal("10"))\n    except ValueError:\n        pass\n'
}


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


git("checkout", "-q", "-b", BRANCH)
for path, text in FILES.items():
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
git("add", "-A")
git("commit", "-q", "-m", SUBJECT, "-m", BODY)
