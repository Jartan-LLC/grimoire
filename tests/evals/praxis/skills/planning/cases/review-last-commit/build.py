"""Build this case's history: run by the eval runner inside the fixture repository."""

import pathlib
import subprocess

pathlib.Path("stats.py").write_text(
    "def mean(values):\n    return sum(values) / len(values)\n\n\n"
    "def median(values):\n    values = sorted(values)\n    return values[len(values) // 2]\n"
)
subprocess.run(["git", "commit", "-qam", "feat: add median"], check=True, capture_output=True)
