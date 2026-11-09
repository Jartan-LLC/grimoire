# notekit

A command-line notebook. Each command is a module under `notekit/commands/`:

- `add.py`: `add <text> [#tag ...]` stores a note and prints its id.
- `search.py`: `search <words>` prints the ids and first lines of notes holding every
  word, case-insensitive; `#tag` words match tags only.
- `export.py`: `export md|json` prints every note as Markdown sections or a JSON array.

Each command has its own tests in `tests/test_<command>.py`.
