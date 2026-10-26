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


git("checkout", "-q", "-b", "feature/logging")
write(
    "applog/__init__.py",
    '"""Logging setup."""\n\nimport logging\nimport pathlib\n\n\ndef setup(name: str) -> logging.Logger:\n    """A logger writing to `<name>.log` beside this file."""\n    logger = logging.getLogger(name)\n    logger.addHandler(logging.FileHandler(pathlib.Path(__file__).with_name(f"{name}.log")))\n    return logger\n',
)
write(
    "tests/test_applog.py",
    'from applog import setup\n\n\ndef test_setup() -> None:\n    assert setup("t").handlers\n',
)
commit(
    "feat(applog): log to a file beside the script",
    "A file keeps the logs after the terminal closes.",
)
push_to_origin("feature/logging")
