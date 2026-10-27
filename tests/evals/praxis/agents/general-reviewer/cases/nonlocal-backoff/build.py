"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

CHANGE = json.loads(
    '{"branch": "feature/timeout-budget", "subject": "feat(client): fail a GET that runs past its time budget", "body": "The sync jobs run on a 10-second schedule, so a fetch must not outlast it.", "files": {"fetchkit/client.py": "\\"\\"\\"Fetch a resource, retrying transient failures.\\"\\"\\"\\n\\nimport time\\n\\nfrom fetchkit import transport\\nfrom fetchkit.retry import with_retries\\nfrom fetchkit.transport import Response\\n\\nBUDGET_S = 10.0\\n\\n\\nclass OverBudget(Exception):\\n    \\"\\"\\"A GET, retries included, took longer than its budget.\\"\\"\\"\\n\\n\\ndef get(url: str, budget_s: float = BUDGET_S) -> Response:\\n    \\"\\"\\"GET `url`, retrying 5xx responses, within `budget_s` seconds.\\"\\"\\"\\n    started = time.monotonic()\\n    # with_retries sleeps 0.5 s and then 1 s between its three attempts, so retrying alone costs 1.5 s.\\n    response = with_retries(lambda: transport.send(url))\\n    if time.monotonic() - started > budget_s:\\n        raise OverBudget(url)\\n    return response\\n"}, "rename": null}'
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
