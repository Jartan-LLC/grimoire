Start one general-purpose subagent with exactly this brief, then pass on what it reports.

# Brief: notekit commands

Depth: two levels below the main thread.
You are at the depth limit: build your part and never split.

Scope: write only notekit/commands/add.py, notekit/commands/search.py,
notekit/commands/export.py and tests/test_add.py, tests/test_search.py,
tests/test_export.py; everything else is read-only.
Contract, read-only: notekit/store.py.
Test command, your tests only: python3 -m pytest -q tests/test_add.py tests/test_search.py tests/test_export.py
Requirements: README.md, every bullet.
Settled decisions you touch: each command is a function `run(store, args: list[str]) -> str`.
Skills to load: none named.
Do not stage, commit, push or switch branches. Ask no questions; report instead.

Report: outcome; the test command and its terse output; files written.
