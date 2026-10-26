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


git("checkout", "-q", "-b", "feature/toml-settings")
write(
    "settings/__init__.py",
    '"""App settings."""\n\nimport pathlib\nimport tomllib\n\n\ndef load(path: pathlib.Path) -> dict[str, object]:\n    """Settings from a TOML file."""\n    return tomllib.loads(path.read_text())\n',
)
write("settings/migrate.py", '"""Convert settings.json to settings.toml once."""\n')
write(
    "tests/test_settings.py",
    'import pathlib\n\nfrom settings import load\n\n\ndef test_load(tmp_path: pathlib.Path) -> None:\n    (tmp_path / "s.toml").write_text("")\n    assert load(tmp_path / "s.toml") == {}\n',
)
commit(
    "feat(settings): read settings from TOML", "TOML allows comments, which operators asked for."
)
