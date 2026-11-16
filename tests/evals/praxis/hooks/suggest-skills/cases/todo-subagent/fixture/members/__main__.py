"""Load a member export and print how many members it holds: `python -m members FILE`."""

import sys

from members.load import load_members

with open(sys.argv[1], encoding="utf-8") as export:
    print(f"{len(load_members(export))} members")
