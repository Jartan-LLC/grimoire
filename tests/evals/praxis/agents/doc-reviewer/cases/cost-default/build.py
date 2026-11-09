"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/timeout"
COMMITS = json.loads(
    '[{"subject": "feat(cli): add --timeout", "body": "", "files": {"fetchy/cli.py": "\\"\\"\\"fetchy URL [--timeout SECONDS]: download URL. --timeout defaults to 60 seconds.\\"\\"\\"\\n\\nimport argparse\\nimport pathlib\\nimport urllib.request\\n\\n\\ndef main() -> None:\\n    parser = argparse.ArgumentParser(prog=\\"fetchy\\")\\n    parser.add_argument(\\"url\\")\\n    parser.add_argument(\\"--timeout\\", type=float, default=60.0, metavar=\\"SECONDS\\")\\n    args = parser.parse_args()\\n    with urllib.request.urlopen(args.url, timeout=args.timeout) as response:\\n        name = pathlib.PurePosixPath(args.url).name or \\"index.html\\"\\n        pathlib.Path(name).write_bytes(response.read())\\n"}}, {"subject": "fix(cli): retry once when an old proxy rejects a TLS session ticket", "body": "", "files": {"fetchy/cli.py": "\\"\\"\\"fetchy URL [--timeout SECONDS]: download URL. --timeout defaults to 60 seconds.\\"\\"\\"\\n\\nimport argparse\\nimport pathlib\\n\\nfrom fetchy import tls\\n\\n\\ndef main() -> None:\\n    parser = argparse.ArgumentParser(prog=\\"fetchy\\")\\n    parser.add_argument(\\"url\\")\\n    parser.add_argument(\\"--timeout\\", type=float, default=60.0, metavar=\\"SECONDS\\")\\n    args = parser.parse_args()\\n    with tls.urlopen(args.url, args.timeout) as response:\\n        name = pathlib.PurePosixPath(args.url).name or \\"index.html\\"\\n        pathlib.Path(name).write_bytes(response.read())\\n", "fetchy/tls.py": "\\"\\"\\"Retry once when an old proxy rejects a TLS session ticket.\\"\\"\\"\\n\\nimport http.client\\nimport ssl\\nimport urllib.request\\n\\n\\ndef urlopen(url: str, timeout: float) -> http.client.HTTPResponse:\\n    try:\\n        return urllib.request.urlopen(url, timeout=timeout)\\n    except ssl.SSLError:\\n        context = ssl.create_default_context()\\n        context.options |= ssl.OP_NO_TICKET\\n        return urllib.request.urlopen(url, timeout=timeout, context=context)\\n"}}, {"subject": "docs: document --timeout", "body": "", "files": {"docs/usage.md": "# Usage\\n\\n`fetchy URL` downloads `URL` into the current directory.\\n\\n`--timeout SECONDS` sets how long to wait for the server. It defaults to 30 seconds.\\n"}}]'
)


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


git("checkout", "-q", "-b", BRANCH)
for commit in COMMITS:
    for path, text in commit["files"].items():
        target = pathlib.Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    git("add", "-A")
    git("commit", "-q", "-m", commit["subject"], "-m", commit["body"])
