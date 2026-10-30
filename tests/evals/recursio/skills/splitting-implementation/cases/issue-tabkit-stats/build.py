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
    ".claude/workspace/issue-31/plan.md",
    "# Plan: tabkit stats (#31)\n\n## Steps\n\n1. `src/tabkit/infer.py`: `infer_type(values) -> ColumnType` for integer, decimal, date, boolean\n   and text, with tests.\n2. `src/tabkit/summary.py`: one summary per type, returned as a `ColumnSummary`, with tests.\n3. `src/tabkit/histogram.py`: a text histogram of a numeric column (10 bins, 40 characters wide),\n   with tests.\n4. `src/tabkit/cli.py`: the `stats` subcommand with text and `--json` output, with tests.\n\n## Verification\n\n- `python3 -m pytest -q`\n",
)
