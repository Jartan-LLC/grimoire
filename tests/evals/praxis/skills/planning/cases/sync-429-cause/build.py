"""Build this case's history: run by the eval runner inside the fixture repository."""

import os
import pathlib
import subprocess

sync = pathlib.Path("sync.py")
sync.write_text(sync.read_text().replace("PAGE_SIZE = 100", "PAGE_SIZE = 1"))
when = "2026-10-27T10:00:00"
env = {**os.environ, "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}
message = "debug: one order per page while chasing the bad record"
subprocess.run(["git", "commit", "-qam", message], check=True, env=env)
