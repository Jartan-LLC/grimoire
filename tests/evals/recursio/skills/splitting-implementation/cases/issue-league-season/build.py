"""Build this case's history: run by the eval runner inside the fixture repository."""

import pathlib
import subprocess


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


def write(path: str, text: str) -> None:
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)


write(
    ".claude/workspace/issue-44/plan.md",
    "# Plan: leaguekit season tooling (#44)\n\n## Steps\n\n1. `src/leaguekit/schedule.py`: the circle-method round robin, single and double, with its home and\n   away orientation, byes, break counts and round dates around blackouts, with\n   `tests/test_schedule.py`.\n2. `src/leaguekit/standings.py`: `table()` with configurable points, shoot-out points and the\n   tiebreaker chain, head-to-head mini tables recomputed per level group, and `form()`, with\n   `tests/test_standings.py`.\n3. `src/leaguekit/ratings.py`: expected score, margin multiplier, `update()`, `rate()` over a\n   season and `regress()` between seasons, with `tests/test_ratings.py`.\n4. `src/leaguekit/playoffs.py`: seed order, first round with byes, `decide()` for one and two legs,\n   `run_bracket()` with the third-place match, and `render()`, with `tests/test_playoffs.py`.\n5. `src/leaguekit/cli.py`: the CSV readers and the `schedule`, `table`, `ratings` and `bracket`\n   subcommands with their exit statuses, with `tests/test_cli.py`.\n\n## Verification\n\n- `python3 -m pytest -q`\n",
)
