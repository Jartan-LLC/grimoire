"""Build this case's history: run by the eval runner inside the fixture repository."""

import os
import pathlib
import subprocess

feeds = pathlib.Path("feeds.txt")
feeds.write_text(feeds.read_text() + "https://blog.example.com/feed\n")
when = "2026-11-03T19:05:00"
env = {**os.environ, "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}
message = "feat: read my blog over https"
subprocess.run(["git", "commit", "-qam", message], check=True, env=env)
