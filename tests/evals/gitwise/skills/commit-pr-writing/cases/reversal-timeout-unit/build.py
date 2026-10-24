"""Build this case's history: run by the eval runner inside the fixture repository."""

import pathlib
import subprocess


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


def write(path: str, text: str) -> None:
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)


def commit(subject: str, body: str = "") -> None:
    git("add", "-A")
    git("commit", "-q", "-m", subject, *(["-m", body] if body else []))


def push_to_origin(*branches: str) -> None:
    git("init", "-q", "--bare", "../origin.git")
    git("remote", "add", "origin", "../origin.git")
    git("push", "-q", "-u", "origin", *branches)


def habit(package: str, commits: list[tuple[str, str]]) -> None:
    """Earlier commits on the current branch, each adding a small helper, with these messages."""
    for n, (subject, body) in enumerate(commits, 1):
        write(
            f"{package}/helper_{n}.py",
            f'"""Helper {n}."""\n\n\ndef helper_{n}() -> int:\n    """Return {n}."""\n    return {n}\n',
        )
        commit(subject, body)


git("checkout", "-q", "-b", "feature/connect")
write(
    "netlib/__init__.py",
    '"""Connections."""\n\n\ndef connect(host: str, timeout: int = 5000) -> dict[str, object]:\n    """Connection settings for `host`; `timeout` in milliseconds."""\n    return {"host": host, "timeout_s": timeout / 1000}\n',
)
write(
    "tests/test_netlib.py",
    'from netlib import connect\n\n\ndef test_timeout() -> None:\n    assert connect("h", timeout=2000)["timeout_s"] == 2\n',
)
commit(
    "feat(netlib): take the connect timeout in milliseconds",
    "Callers must pass timeout= in milliseconds.",
)
push_to_origin("feature/connect")
