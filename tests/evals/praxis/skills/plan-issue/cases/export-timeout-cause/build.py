"""Build this case's history: run by the eval runner inside the fixture repository."""

import os
import pathlib
import subprocess

config = pathlib.Path("ledgerpush/config.py")
config.write_text(config.read_text().replace("TIMEOUT = 30", "TIMEOUT = 0.3"))
when = "2026-11-02T08:30:00"
env = {**os.environ, "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}
message = "chore: tighten timeouts so the health check fails fast"
subprocess.run(["git", "commit", "-qam", message], check=True, env=env)
