"""Build this case's history: run by the eval runner inside the fixture repository."""

import pathlib
import subprocess

BRANCH = "feature/csv-import"
SUBJECT = "feat(store): import stock levels from a CSV export"
BODY = "The warehouse sends a nightly CSV; this loads it into the store."
FILES = {
    "stockroom/importer.py": '"""Load stock levels from the warehouse\'s nightly CSV export."""\n\nimport csv\n\nfrom stockroom.store import Store\n\n\ndef import_levels(path, store=Store(), skipped=[]):\n    """Read `path` into `store`; rows that cannot be read go to `skipped`."""\n    f = open(path)\n    for row in csv.reader(f):\n        try:\n            store.put(row[0], int(row[1]))\n        except:\n            skipped.append(row)\n    return store, skipped\n'
}


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


git("checkout", "-q", "-b", BRANCH)
for path, text in FILES.items():
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
git("add", "-A")
git("commit", "-q", "-m", SUBJECT, "-m", BODY)
