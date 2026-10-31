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
    ".claude/workspace/issue-81/plan.md",
    "# Plan: zonekit zone tooling (#81)\n\n## Steps\n\n1. `src/zonekit/parse.py`: `parse_zone()` for RFC 1035 master files: directives, parentheses,\n   comments, quoted strings and escapes, carried owner, TTL and class, and per-type rdata, with\n   numbered line errors, with `tests/test_parse.py`.\n2. `src/zonekit/validate.py`: `validate()` with the SOA, apex NS, CNAME, target, glue, TTL,\n   duplicate, SRV, CAA and out-of-zone checks, with `tests/test_validate.py`.\n3. `src/zonekit/wire.py`: `encode_message()` with name compression and per-type rdata, and\n   `decode_message()` with its `WireError` cases, with `tests/test_wire.py`.\n4. `src/zonekit/diff.py`: `diff_zones()` in canonical order with TTL-only changes and the serial\n   warning, `rdata_text()` and `render_diff()`, with `tests/test_diff.py`.\n5. `src/zonekit/cli.py`: the `check`, `diff` and `encode` subcommands with their output and exit\n   statuses, with `tests/test_cli.py`.\n\n## Verification\n\n- `python3 -m pytest -q`\n",
)
