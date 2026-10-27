"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

CHANGE = json.loads(
    '{"branch": "feature/retry-429", "subject": "feat(retry): retry rate-limited responses too", "body": "Upstream answers 429 under load; those are worth another attempt.", "files": {"fetchkit/retry.py": "\\"\\"\\"Retry a request that failed for a reason that may pass.\\"\\"\\"\\n\\nimport time\\nfrom collections.abc import Callable\\n\\nfrom fetchkit.transport import Response\\n\\nMAX_ATTEMPTS = 3\\nBASE_DELAY_S = 0.5\\n\\n\\ndef _transient(response: Response) -> bool:\\n    return response.status > 500 or response.status == 429\\n\\n\\ndef with_retries(call: Callable[[], Response], sleep: Callable[[float], None] = time.sleep) -> Response:\\n    \\"\\"\\"`call()`, retried with exponential backoff while it fails with a 5xx or 429 status.\\"\\"\\"\\n    response = call()\\n    for attempt in range(1, MAX_ATTEMPTS):\\n        if not _transient(response):\\n            return response\\n        sleep(BASE_DELAY_S * 2 ** (attempt - 1))\\n        response = call()\\n    return response\\n"}, "rename": null}'
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
