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
    ".claude/workspace/issue-58/plan.md",
    "# Plan: exports (#58)\n\n## Steps\n\n1. `src/export/filter.js`: `filterEvents(events, { since, tag })`, with tests.\n2. `src/export/csv.js`: `toCsv(events)` per RFC 4180, with tests.\n3. `src/export/ndjson.js`: `toNdjson(events)`, with tests.\n4. `src/export/ics.js`: `toIcs(events)` per RFC 5545 (folding, escaping), with tests.\n5. `bin/eventlog.js`: the `export` command and its flags, with a test.\n\n## Verification\n\n- `npm test`\n",
)
