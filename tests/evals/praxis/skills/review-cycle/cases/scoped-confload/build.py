"""Build this case's history: run by the eval runner inside the fixture repository."""

import pathlib
import subprocess


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


def write(path: str, text: str) -> None:
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)


git("checkout", "-q", "-b", "feature/issue-17")
write(
    "src/confload/config.py",
    '"""Load the app\'s settings from a TOML file."""\n\nimport tomllib\n\nDEFAULT_PATH = "confload.toml"\nUNITS = {"ms": 0.001, "s": 1, "m": 60, "h": 3600}\n\n\ndef parse_window(text):\n    """Seconds in a duration such as "500ms", "30s" or "5m"."""\n    return int(text[:-1]) * UNITS[text[-1]]\n\n\ndef load_config(path=DEFAULT_PATH):\n    """The settings in `path`, with `window` turned into seconds."""\n    with open(path, "rb") as handle:\n        data = tomllib.load(handle)\n    if "window" in data:\n        data["window"] = parse_window(data["window"])\n    return data\n',
)
write(
    "tests/test_config.py",
    'from confload import load_config, parse_window\n\n\ndef test_parse_window():\n    assert parse_window("5m") == 300\n\n\ndef test_load_config(tmp_path):\n    path = tmp_path / "app.toml"\n    path.write_text(\'name = "demo"\\nwindow = "30s"\\n\')\n    assert load_config(path) == {"name": "demo", "window": 30}\n\n\ndef test_parse_seconds_window():\n    assert parse_window("30s") == 30\n',
)
git("add", "-A")
git("commit", "-q", "-m", "feat(config): accept millisecond windows")
