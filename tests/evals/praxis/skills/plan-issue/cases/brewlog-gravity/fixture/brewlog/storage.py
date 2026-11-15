"""Brews on disk: one row per brew, `date,name,style`."""

# Written by hand before the project used the csv module: a comma in a name breaks its row.
# Switching to csv.reader and csv.writer changes how a name holding a quote is read back.
import os

FIELDS = ["date", "name", "style"]


def path() -> str:
    return os.environ.get("BREWLOG_FILE") or os.path.expanduser("~/.brewlog.csv")


def load(file: str) -> list[dict[str, str]]:
    if not os.path.exists(file):
        return []
    brews = []
    with open(file, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line:
                brews.append(dict(zip(FIELDS, line.split(","))))
    return brews


def append(file: str, brew: dict[str, str]) -> None:
    with open(file, "a", encoding="utf-8") as f:
        f.write(",".join(brew[k] for k in FIELDS) + "\n")
