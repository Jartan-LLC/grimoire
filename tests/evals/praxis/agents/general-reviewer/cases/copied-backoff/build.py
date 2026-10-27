"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

CHANGE = json.loads(
    '{"branch": "feature/poll", "subject": "feat(poll): poll a URL until it reports done", "body": "Export jobs finish asynchronously; the sync job polls their status URL.", "files": {"fetchkit/poll.py": "\\"\\"\\"Poll a status URL until the job behind it finishes.\\"\\"\\"\\n\\nimport time\\nfrom collections.abc import Callable\\n\\nfrom fetchkit.client import get\\n\\nMAX_ATTEMPTS = 3\\nBASE_DELAY_S = 0.5\\n\\n\\ndef poll(url: str, sleep: Callable[[float], None] = time.sleep) -> bool:\\n    \\"\\"\\"Whether the job at `url` reported done within the attempts allowed.\\"\\"\\"\\n    response = get(url)\\n    for attempt in range(1, MAX_ATTEMPTS):\\n        if response.body == \\"done\\":\\n            return True\\n        sleep(BASE_DELAY_S * 2 ** (attempt - 1))\\n        response = get(url)\\n    return response.body == \\"done\\"\\n"}, "rename": null}'
)


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


git("init", "-q", "--bare", "../origin.git")
git("remote", "add", "origin", "../origin.git")
git("push", "-q", "-u", "origin", "main")
git("checkout", "-q", "-b", CHANGE["branch"])
if CHANGE["rename"]:
    git("mv", *CHANGE["rename"])
for path, text in CHANGE["files"].items():
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
git("add", "-A")
git("commit", "-q", "-m", CHANGE["subject"], "-m", CHANGE["body"])
