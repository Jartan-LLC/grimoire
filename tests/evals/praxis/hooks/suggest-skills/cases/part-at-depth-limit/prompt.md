Start one general-purpose subagent with exactly this brief, then tell me what it reports.

# Brief: exportkit formats

Depth: two levels below the main thread.
You are at the depth limit: build your part and never split.

Scope: write only exportkit/formats/csv.py, exportkit/formats/json.py,
exportkit/formats/xml.py and tests/test_csv.py, tests/test_json.py, tests/test_xml.py;
everything else is read-only.
Contract, read-only: exportkit/model.py.
Test command, your tests only: python3 -m pytest -q tests/test_csv.py tests/test_json.py tests/test_xml.py
Requirements: README.md, every bullet.
Settled decisions you touch: none.
Skills to load: none named.
Do not stage, commit, push or switch branches. Ask no questions; report instead.

Report: outcome; the test command and its terse output; files written.
