"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

CHANGE = json.loads(
    '{"branch": "feature/drop-response-cache", "subject": "refactor(client): drop the response cache", "body": "The cache served stale prices after upstream corrections, and every caller now handles a failed fetch itself.", "files": {"fetchkit/client.py": "\\"\\"\\"Fetch a resource, retrying transient failures.\\"\\"\\"\\n\\nfrom fetchkit import transport\\nfrom fetchkit.retry import with_retries\\nfrom fetchkit.transport import Response\\n\\n\\ndef get(url: str) -> Response:\\n    \\"\\"\\"GET `url`, retrying 5xx responses.\\"\\"\\"\\n    response = with_retries(lambda: transport.send(url))\\n    # When every attempt fails, serve the last good response for this URL instead.\\n    return response\\n"}, "rename": null}'
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
