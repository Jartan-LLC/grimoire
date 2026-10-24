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


git("checkout", "-q", "-b", "feature/sessions")
write(
    "sessions/__init__.py",
    '"""Sessions."""\n\n\ndef start(user: str) -> str:\n    """The cookie value for a new session: the user name itself."""\n    return user\n\n\ndef user_of(cookie: str) -> str:\n    """The user a cookie belongs to."""\n    return cookie\n',
)
write(
    "tests/test_sessions.py",
    'from sessions import start, user_of\n\n\ndef test_round_trip() -> None:\n    assert user_of(start("ana")) == "ana"\n',
)
commit(
    "feat(sessions): store the session in the cookie",
    "The cookie carries the user name, so no server state is needed.",
)
push_to_origin("feature/sessions")
