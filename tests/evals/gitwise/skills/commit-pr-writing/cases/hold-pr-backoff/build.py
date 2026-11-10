"""Build this case's history: a pushed feature branch, run by the eval runner inside the fixture repository."""

import pathlib
import subprocess


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


def write(path: str, text: str) -> None:
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)


git("init", "-q", "--bare", "-b", "main", "../origin.git")
git("remote", "add", "origin", "../origin.git")
git("push", "-q", "-u", "origin", "main")
git("checkout", "-q", "-b", "feature/retry-backoff")
write(
    "fetcher/backoff.py",
    '"""Retry delays."""\n\n\ndef delays(retries: int, base: float = 0.5) -> list[float]:\n    """The wait before each retry, doubling from `base` seconds."""\n    return [base * 2**n for n in range(retries)]\n',
)
write(
    "tests/test_backoff.py",
    "from fetcher.backoff import delays\n\n\ndef test_doubles() -> None:\n    assert delays(3) == [0.5, 1.0, 2.0]\n",
)
git("add", "-A")
git(
    "commit",
    "-q",
    "-m",
    "feat(fetcher): wait longer before each retry",
    "-m",
    "Retrying at once hammered a server that was already failing.",
)
git("push", "-q", "-u", "origin", "feature/retry-backoff")
