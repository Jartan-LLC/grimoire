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


git("checkout", "-q", "-b", "feature/webhooks")
write(
    "hooks/__init__.py",
    '"""Deliver webhooks."""\n\nfrom collections.abc import Callable\n\n\ndef deliver(send: Callable[[], bool]) -> bool:\n    """Send, retrying immediately up to three times on failure."""\n    for _ in range(4):\n        if send():\n            return True\n    return False\n',
)
write(
    "tests/test_hooks.py",
    "from hooks import deliver\n\n\ndef test_success() -> None:\n    assert deliver(lambda: True)\n",
)
commit(
    "feat(hooks): retry failed deliveries immediately",
    "Immediate retries get a webhook through a brief blip fastest.",
)
push_to_origin("feature/webhooks")
