"""Build this case's history: run by the eval runner inside the fixture repository."""

import os
import pathlib
import subprocess

alerts = pathlib.Path("stocktake/alerts.py")
alerts.write_text(
    alerts.read_text().replace('cfg["low_stock_threshold"]', 'cfg.get("low_stock", 0)')
)
test = pathlib.Path("tests/test_alerts.py")
test.write_text(test.read_text().replace('"low_stock_threshold": 5', '"low_stock": 5'))
when = "2026-11-05T21:40:00"
env = {**os.environ, "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}
message = "refactor: read settings with defaults so a missing key cannot crash the nightly run"
subprocess.run(["git", "commit", "-qam", message], check=True, env=env)
