"""Build eval suites on disk for the tests."""

import pathlib

SUITE = """
target = "gitwise:commit-pr-writing"
covers = ["plugins/gitwise/skills/commit-pr-writing/**"]

[[metric]]
id = "kept"
direction = "higher"
margin = 0.2

[[metric]]
id = "delivered"
direction = "higher"
margin = 0.2

[pass_rule]
primary = "kept"
rule = "better"
guards = ["delivered"]
min_effect = 0.1
min_samples = 2
"""

KEY = """
split = "dev"
kind = "target"
hints = ["issue number"]

[[fact]]
text = "42"
where = "prompt"

[[check]]
metric = "kept"
artifact = "commits"
present = '#42'

[[check]]
metric = "kept"
artifact = "final"
absent = 'merging is all'

[[check]]
metric = "delivered"
artifact = "delivery"
skill = "gitwise:commit-pr-writing"
write = "commit"
state = "in-context"

[[baseline]]
model = "claude-opus-5-5"
arm = "old"
failures = 2
runs = 3
runner = 2
"""


def write_suite(root: pathlib.Path, suite: str = SUITE, key: str = KEY) -> pathlib.Path:
    (root / "cases" / "c1" / "fixture").mkdir(parents=True)
    (root / "suite.toml").write_text(suite)
    (root / "cases" / "c1" / "prompt.md").write_text("Fix issue 42 and commit.\n")
    (root / "cases" / "c1" / "key.toml").write_text(key)
    (root / "cases" / "c1" / "fixture" / "app.py").write_text("x = 1\n")
    return root
