"""Build this case's history: run by the eval runner inside the fixture repository."""

import pathlib
import subprocess


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


def write(path: str, text: str) -> None:
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)


git("checkout", "-q", "-b", "feature/issue-31")
write(
    "src/ratelimit/window.py",
    '"""A sliding-window rate limiter."""\n\nimport time\n\nUNITS = {"s": 1, "m": 60}\n\n\ndef parse_window(text):\n    """Return (limit, seconds) from a spec such as "10/m"."""\n    count, unit = text.split("/")\n    return int(count), UNITS[unit]\n\n\ndef prune_calls(calls, now, seconds):\n    """The calls still inside the window that ends at `now`."""\n    return [t for t in calls if now - t < seconds]\n\n\nclass SlidingWindow:\n    """Allow at most `limit` calls in any `seconds`-long window."""\n\n    def __init__(self, spec, clock=time.monotonic):\n        self.limit, self.seconds = parse_window(spec)\n        self.clock = clock\n        self.calls = []\n\n    def allow(self):\n        """Record a call and say whether it is within the limit."""\n        now = self.clock()\n        self.calls = prune_calls(self.calls, now, self.seconds)\n        if len(self.calls) >= self.limit:\n            return False\n        self.calls.append(now)\n        return True\n\n    def wait(self):\n        """Seconds until the next call would be allowed, or 0 when one would be allowed now."""\n        now = self.clock()\n        self.calls = prune_calls(self.calls, now, self.seconds)\n        return self.calls[-1] + self.seconds - now\n',
)
write(
    "tests/test_window.py",
    'from ratelimit import SlidingWindow, parse_window\n\n\ndef test_parse_window():\n    assert parse_window("10/m") == (10, 60)\n\n\ndef test_allow_up_to_the_limit():\n    now = [0.0]\n    window = SlidingWindow("2/s", clock=lambda: now[0])\n    assert window.allow()\n    assert window.allow()\n    assert not window.allow()\n    now[0] = 1.5\n    assert window.allow()\n\n\ndef test_wait_1():\n    now = [0.0]\n    window = SlidingWindow("2/s", clock=lambda: now[0])\n    assert window.allow()\n    assert window.allow()\n    assert window.wait() == 1.0\n',
)
git("add", "-A")
git("commit", "-q", "-m", "feat(window): say how long until the next call is allowed")
write(
    "src/ratelimit/window.py",
    '"""A sliding-window rate limiter."""\n\nimport time\n\nUNITS = {"s": 1, "m": 60}\n\n\ndef parse_window(text):\n    """Return (limit, seconds) from a spec such as "10/m"."""\n    count, unit = text.split("/")\n    return int(count), UNITS[unit]\n\n\ndef prune_calls(calls, now, seconds):\n    """The calls still inside the window that ends at `now`."""\n    return [t for t in calls if now - t < seconds]\n\n\nclass SlidingWindow:\n    """Allow at most `limit` calls in any `seconds`-long window."""\n\n    def __init__(self, spec, clock=time.monotonic):\n        self.limit, self.seconds = parse_window(spec)\n        self.clock = clock\n        self.calls = []\n\n    def allow(self):\n        """Record a call and say whether it is within the limit."""\n        now = self.clock()\n        self.calls = prune_calls(self.calls, now, self.seconds)\n        if len(self.calls) >= self.limit:\n            return False\n        self.calls.append(now)\n        return True\n\n    def wait(self):\n        """Seconds until the next call would be allowed, or 0 when one would be allowed now."""\n        now = self.clock()\n        self.calls = prune_calls(self.calls, now, self.seconds)\n        if len(self.calls) < self.limit:\n            return 0\n        return self.calls[-1] + self.seconds - now\n',
)
write(
    "tests/test_window.py",
    'from ratelimit import SlidingWindow, parse_window\n\n\ndef test_parse_window():\n    assert parse_window("10/m") == (10, 60)\n\n\ndef test_allow_up_to_the_limit():\n    now = [0.0]\n    window = SlidingWindow("2/s", clock=lambda: now[0])\n    assert window.allow()\n    assert window.allow()\n    assert not window.allow()\n    now[0] = 1.5\n    assert window.allow()\n\n\ndef test_wait_1():\n    now = [0.0]\n    window = SlidingWindow("2/s", clock=lambda: now[0])\n    assert window.allow()\n    assert window.allow()\n    assert window.wait() == 1.0\n\n\ndef test_wait_2():\n    now = [0.0]\n    window = SlidingWindow("2/s", clock=lambda: now[0])\n    assert window.wait() == 0\n    assert window.allow()\n    assert window.wait() == 0\n',
)
write(
    "README.md",
    '# ratelimit\n\n`SlidingWindow("10/m")` allows at most ten calls in any sixty seconds. Each window keeps its own count. When `allow()` says no, `wait()` gives the seconds until a call would be allowed.\n\n## Development\n\nRun the tests with `python3 -m pytest`.\n',
)
git("add", "-A")
git(
    "commit",
    "-q",
    "-m",
    "fix(window): return 0 from wait() while a call is allowed",
    "-m",
    "wait() returned the newest call's remaining time whenever the window held a call, and raised IndexError when it held none. The README now describes wait().",
)
write(
    "tests/test_window.py",
    'from ratelimit import SlidingWindow, parse_window\n\n\ndef test_parse_window():\n    assert parse_window("10/m") == (10, 60)\n\n\ndef test_allow_up_to_the_limit():\n    now = [0.0]\n    window = SlidingWindow("2/s", clock=lambda: now[0])\n    assert window.allow()\n    assert window.allow()\n    assert not window.allow()\n    now[0] = 1.5\n    assert window.allow()\n\n\ndef test_wait_when_the_window_is_full():\n    now = [0.0]\n    window = SlidingWindow("2/s", clock=lambda: now[0])\n    assert window.allow()\n    assert window.allow()\n    assert window.wait() == 1.0\n\n\ndef test_wait_is_zero_while_a_call_is_allowed():\n    now = [0.0]\n    window = SlidingWindow("2/s", clock=lambda: now[0])\n    assert window.wait() == 0\n    assert window.allow()\n    assert window.wait() == 0\n',
)
git("add", "-A")
git("commit", "-q", "-m", "test(window): name the wait tests for what they check")
write(
    ".claude/workspace/issue-31/feature--issue-31/1.md",
    "## Code Review\n\n### Critical Issues\nNone found\n\n### Important Issues\n1. **wait() asks callers to wait even when a call is allowed** -- `src/ratelimit/window.py:40`. It returns a remaining time whenever the window holds a call, below the limit too, and raises `IndexError` when it holds none.\n\nAnswer: fixed in the round-1 commit.\n\n### Minor Issues\n1. **The README does not mention wait()** -- `README.md:3`. Add a sentence.\n\nAnswer: fixed in the round-1 commit.\n\n### Summary\nOne Important and one Minor finding.\n",
)
write(
    ".claude/workspace/issue-31/feature--issue-31/2.md",
    "## Code Review\n\n### Critical Issues\nNone found\n\n### Important Issues\nNone found\n\n### Minor Issues\n1. **The test names do not say what they check** -- `tests/test_window.py:18`. `test_wait_1` and `test_wait_2` number the tests instead of saying what each checks.\n\nAnswer: fixed in the round-2 commit.\n\n### Summary\nOne Minor finding.\n",
)
write(
    ".claude/workspace/issue-31/feature--issue-31/cycle.md",
    "# Review cycle: feature/issue-31\n\nMode: raise\nBase: main\nRound: 2 (addressed)\nClean rounds in a row: 1\nRaised findings: none\nPR: none\n",
)
write(
    ".claude/workspace/issue-31/feature--issue-31/pr.md",
    "feat(window): say how long until the next call is allowed\n\nAdd SlidingWindow.wait(), the seconds until the next call would be allowed.\n\nCloses #31\n",
)
