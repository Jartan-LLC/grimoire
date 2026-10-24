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


git("checkout", "-q", "-b", "feature/get-user")
write(
    "users/__init__.py",
    '"""User lookup."""\n\n_USERS = {1: "ana"}\n\n\ndef get_user(user_id: int) -> str:\n    """The name of user `user_id`."""\n    return _USERS[user_id] if user_id in _USERS else _missing(user_id)\n\n\ndef _missing(user_id: int) -> str:\n    raise LookupError(user_id)\n',
)
write(
    "tests/test_users.py",
    "import pytest\n\nfrom users import get_user\n\n\ndef test_unknown() -> None:\n    with pytest.raises(LookupError):\n        get_user(9)\n",
)
commit(
    "feat(users): raise LookupError for an unknown user",
    "Callers must catch LookupError from get_user() when the id may not exist.",
)
push_to_origin("feature/get-user")
