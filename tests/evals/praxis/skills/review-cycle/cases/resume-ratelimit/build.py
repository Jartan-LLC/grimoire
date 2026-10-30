"""Build this case's history: run by the eval runner inside the fixture repository."""

import pathlib
import subprocess


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


def write(path: str, text: str) -> None:
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)


git("checkout", "-q", "-b", "feature/issue-23")
write(
    "src/ratelimit/window.py",
    '"""A sliding-window rate limiter."""\n\nimport time\n\nUNITS = {"s": 1, "m": 60, "h": 360}\n\n\ndef parse_window(text):\n    """Return (limit, seconds) from a spec such as "10/m"."""\n    count, unit = text.split("/")\n    return int(count), UNITS.get(unit, 1)\n\n\ndef prune_calls(calls, now, seconds):\n    """The calls still inside the window that ends at `now`."""\n    return [t for t in calls if now - t < seconds]\n\n\nclass SlidingWindow:\n    """Allow at most `limit` calls in any `seconds`-long window."""\n\n    def __init__(self, spec, clock=time.monotonic):\n        self.limit, self.seconds = parse_window(spec)\n        self.clock = clock\n        self.calls = []\n\n    def allow(self):\n        """Record a call and say whether it is within the limit."""\n        now = self.clock()\n        self.calls = prune_calls(self.calls, now, self.seconds)\n        if len(self.calls) >= self.limit:\n            return False\n        self.calls.append(now)\n        return True\n',
)
write(
    "tests/test_window.py",
    'from ratelimit import SlidingWindow, parse_window\n\n\ndef test_parse_window():\n    assert parse_window("10/m") == (10, 60)\n\n\ndef test_allow_up_to_the_limit():\n    now = [0.0]\n    window = SlidingWindow("2/s", clock=lambda: now[0])\n    assert window.allow()\n    assert window.allow()\n    assert not window.allow()\n    now[0] = 1.5\n    assert window.allow()\n\n\ndef test_parse_window_2():\n    assert parse_window("100/h") == (100, 360)\n',
)
git("add", "-A")
git("commit", "-q", "-m", "feat(window): accept an hourly unit")
write(
    "src/ratelimit/window.py",
    '"""A sliding-window rate limiter."""\n\nimport time\n\nUNITS = {"s": 1, "m": 60, "h": 360}\n\n\ndef parse_window(text):\n    """Return (limit, seconds) from a spec such as "10/m"."""\n    count, unit = text.split("/")\n    if unit not in UNITS:\n        raise ValueError(f"unknown unit {unit!r} in {text!r}")\n    return int(count), UNITS[unit]\n\n\ndef prune_calls(calls, now, seconds):\n    """The calls still inside the window that ends at `now`."""\n    return [t for t in calls if now - t < seconds]\n\n\nclass SlidingWindow:\n    """Allow at most `limit` calls in any `seconds`-long window."""\n\n    def __init__(self, spec, clock=time.monotonic):\n        self.limit, self.seconds = parse_window(spec)\n        self.clock = clock\n        self.calls = []\n\n    def allow(self):\n        """Record a call and say whether it is within the limit."""\n        now = self.clock()\n        self.calls = prune_calls(self.calls, now, self.seconds)\n        if len(self.calls) >= self.limit:\n            return False\n        self.calls.append(now)\n        return True\n',
)
write(
    "tests/test_window.py",
    'import pytest\nfrom ratelimit import SlidingWindow, parse_window\n\n\ndef test_parse_window():\n    assert parse_window("10/m") == (10, 60)\n\n\ndef test_allow_up_to_the_limit():\n    now = [0.0]\n    window = SlidingWindow("2/s", clock=lambda: now[0])\n    assert window.allow()\n    assert window.allow()\n    assert not window.allow()\n    now[0] = 1.5\n    assert window.allow()\n\n\ndef test_parse_window_2():\n    assert parse_window("100/h") == (100, 360)\n\n\ndef test_parse_window_3():\n    with pytest.raises(ValueError, match="unknown unit"):\n        parse_window("100/d")\n',
)
write(
    "README.md",
    '# ratelimit\n\n`SlidingWindow("10/m")` allows at most ten calls in any sixty seconds; the units are `s`, `m` and `h` (an hour). Each window keeps its own count.\n\n## Development\n\nRun the tests with `python3 -m pytest`.\n',
)
git("add", "-A")
git(
    "commit",
    "-q",
    "-m",
    "fix(window): reject a window with an unknown unit",
    "-m",
    "UNITS.get(unit, 1) read any unknown unit as seconds, so 100/d allowed 100 calls a second. The README now lists the units.",
)
write(
    "tests/test_window.py",
    'import pytest\nfrom ratelimit import SlidingWindow, parse_window\n\n\ndef test_parse_window():\n    assert parse_window("10/m") == (10, 60)\n\n\ndef test_allow_up_to_the_limit():\n    now = [0.0]\n    window = SlidingWindow("2/s", clock=lambda: now[0])\n    assert window.allow()\n    assert window.allow()\n    assert not window.allow()\n    now[0] = 1.5\n    assert window.allow()\n\n\ndef test_parse_hourly_window():\n    assert parse_window("100/h") == (100, 360)\n\n\ndef test_parse_window_rejects_an_unknown_unit():\n    with pytest.raises(ValueError, match="unknown unit"):\n        parse_window("100/d")\n',
)
git("add", "-A")
git("commit", "-q", "-m", "test(window): name the window tests for what they check")
write(
    ".claude/workspace/issue-23/feature--issue-23/1.md",
    '## Code Review\n\n### Critical Issues\nNone found\n\n### Important Issues\n1. **An unknown unit silently counts as seconds** -- `src/ratelimit/window.py:11`. `UNITS.get(unit, 1)` turns `"100/d"` into 100 calls a second instead of rejecting it.\n\nAnswer: fixed in the round-1 commit.\n\n### Minor Issues\n1. **The README does not mention the hourly unit** -- `README.md:3`. Add a sentence.\n\nAnswer: fixed in the round-1 commit.\n\n### Summary\nOne Important and one Minor finding.\n',
)
write(
    ".claude/workspace/issue-23/feature--issue-23/2.md",
    "## Code Review\n\n### Critical Issues\nNone found\n\n### Important Issues\nNone found\n\n### Minor Issues\n1. **The test names do not say what they check** -- `tests/test_window.py:19`. `test_parse_window_2` and `test_parse_window_3` number the tests instead of saying what each checks.\n\nAnswer: fixed in the round-2 commit.\n\n### Summary\nOne Minor finding.\n",
)
write(
    ".claude/workspace/issue-23/feature--issue-23/cycle.md",
    "# Review cycle: feature/issue-23\n\nMode: raise\nBase: main\nRound: 2 (addressed)\nClean rounds in a row: 1\nRaised findings: none\nPR: none\n",
)
write(
    ".claude/workspace/issue-23/feature--issue-23/pr.md",
    "feat(window): accept an hourly unit\n\nAccept hourly limits such as 100/h.\n\nCloses #23\n",
)
