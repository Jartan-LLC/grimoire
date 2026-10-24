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


git("checkout", "-q", "-b", "feature/config")
write(
    "settings/__init__.py",
    '"""Load settings."""\n\nimport json\nimport pathlib\n\n\ndef load(path: pathlib.Path) -> dict[str, object]:\n    """Settings from `path`."""\n    return json.loads(path.read_text())\n',
)
write(
    "tests/test_settings.py",
    'import pathlib\n\nfrom settings import load\n\n\ndef test_load(tmp_path: pathlib.Path) -> None:\n    (tmp_path / "config.json").write_text(\'{"debug": true}\')\n    assert load(tmp_path / "config.json") == {"debug": True}\n',
)
commit(
    "feat(settings): read the config from JSON",
    "JSON is in the standard library, so no dependency is needed.",
)
push_to_origin("feature/config")
