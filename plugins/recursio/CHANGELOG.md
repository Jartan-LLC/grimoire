# Changelog

## 1.1.4

- `recursive-implementer` writes comments only for what the code cannot say, docstrings where the language or the project asks for them, and no section dividers. It no longer adds a one-line comment to every public function.

## 1.1.3

- The README documents the SessionStart hook that installs the Codex agent roles.

## 1.1.2

- `recursive-implement` no longer sets `disable-model-invocation: true`, so an
  unprefixed `/recursive-implement` runs it and Claude can start it too.
