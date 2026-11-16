# TODO

- [ ] README: the Running section still says `python load.py members.csv`. Since the code
      moved into the `members` package it's `python -m members members.csv`.
- [ ] `load_members` stops at the first line it can't read, so one typo in a 3,000-line
      export loses the whole import. Load every good line, and at the end tell the office
      about every bad one: its line number and what was wrong with it.
