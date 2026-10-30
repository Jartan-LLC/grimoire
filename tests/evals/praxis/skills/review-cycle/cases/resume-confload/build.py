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
    '"""Load the app\'s settings from a TOML file."""\n\nimport tomllib\n\nDEFAULT_PATH = "confload.toml"\nUNITS = {"ms": 1, "s": 1, "m": 60, "h": 3600}\n\n\ndef parse_window(text):\n    """Seconds in a duration such as "500ms", "30s" or "5m"."""\n    return int(text[:-1]) * UNITS[text[-1]]\n\n\ndef load_config(path=DEFAULT_PATH):\n    """The settings in `path`, with `window` turned into seconds."""\n    with open(path, "rb") as handle:\n        data = tomllib.load(handle)\n    if "window" in data:\n        data["window"] = parse_window(data["window"])\n    return data\n',
)
write(
    "tests/test_config.py",
    'from confload import load_config, parse_window\n\n\ndef test_parse_window():\n    assert parse_window("5m") == 300\n\n\ndef test_load_config(tmp_path):\n    path = tmp_path / "app.toml"\n    path.write_text(\'name = "demo"\\nwindow = "30s"\\n\')\n    assert load_config(path) == {"name": "demo", "window": 30}\n\n\ndef test_parse_window_2():\n    assert parse_window("30s") == 30\n\n\ndef test_parse_window_3():\n    assert parse_window("2h") == 7200\n',
)
git("add", "-A")
git("commit", "-q", "-m", "feat(config): accept millisecond windows")
write(
    "src/confload/config.py",
    '"""Load the app\'s settings from a TOML file."""\n\nimport tomllib\n\nDEFAULT_PATH = "confload.toml"\nUNITS = {"ms": 0.001, "s": 1, "m": 60, "h": 3600}\n\n\ndef parse_window(text):\n    """Seconds in a duration such as "500ms", "30s" or "5m"."""\n    return int(text[:-1]) * UNITS[text[-1]]\n\n\ndef load_config(path=DEFAULT_PATH):\n    """The settings in `path`, with `window` turned into seconds."""\n    with open(path, "rb") as handle:\n        data = tomllib.load(handle)\n    if "window" in data:\n        data["window"] = parse_window(data["window"])\n    return data\n',
)
write(
    "README.md",
    '# confload\n\n`load_config()` reads the app\'s settings from `confload.toml` and turns `window` (such as `"30s"` or `"500ms"`) into seconds.\n\n## Development\n\nRun the tests with `python3 -m pytest`.\n',
)
git("add", "-A")
git(
    "commit",
    "-q",
    "-m",
    "fix(config): count a millisecond as a thousandth of a second",
    "-m",
    "UNITS gave ms the same factor as s. The README now gives a millisecond example.",
)
write(
    "tests/test_config.py",
    'from confload import load_config, parse_window\n\n\ndef test_parse_window():\n    assert parse_window("5m") == 300\n\n\ndef test_load_config(tmp_path):\n    path = tmp_path / "app.toml"\n    path.write_text(\'name = "demo"\\nwindow = "30s"\\n\')\n    assert load_config(path) == {"name": "demo", "window": 30}\n\n\ndef test_parse_seconds_window():\n    assert parse_window("30s") == 30\n\n\ndef test_parse_hours_window():\n    assert parse_window("2h") == 7200\n',
)
git("add", "-A")
git("commit", "-q", "-m", "test(config): name the window tests for what they parse")
write(
    ".claude/workspace/issue-17/feature--issue-17/1.md",
    '## Code Review\n\n### Critical Issues\nNone found\n\n### Important Issues\n1. **A millisecond counts as a whole second** -- `src/confload/config.py:6`. `UNITS["ms"]` is `1`, the same factor as a second; a millisecond is `0.001`.\n\nAnswer: fixed in the round-1 commit.\n\n### Minor Issues\n1. **The README does not mention millisecond windows** -- `README.md:3`. Add a sentence.\n\nAnswer: fixed in the round-1 commit.\n\n### Summary\nOne Important and one Minor finding.\n',
)
write(
    ".claude/workspace/issue-17/feature--issue-17/2.md",
    "## Code Review\n\n### Critical Issues\nNone found\n\n### Important Issues\nNone found\n\n### Minor Issues\n1. **The test names do not say what they check** -- `tests/test_config.py:14`. `test_parse_window_2` and `test_parse_window_3` number the tests instead of saying which window each parses.\n\nAnswer: fixed in the round-2 commit.\n\n### Summary\nOne Minor finding.\n",
)
write(
    ".claude/workspace/issue-17/feature--issue-17/cycle.md",
    "# Review cycle: feature/issue-17\n\nMode: raise\nBase: main\nRound: 2 (addressed)\nClean rounds in a row: 1\nRaised findings: none\nPR: none\n",
)
write(
    ".claude/workspace/issue-17/feature--issue-17/pr.md",
    "feat(config): accept millisecond windows\n\nAccept millisecond windows such as 500ms.\n\nCloses #17\n",
)
