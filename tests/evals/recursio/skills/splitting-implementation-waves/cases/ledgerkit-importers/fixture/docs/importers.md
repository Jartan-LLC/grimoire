# Importers

`ledgerkit/importers/` holds one module per bank export format. Each format is specified in its
own file under `docs/formats/`; the file's name is the module's name (`docs/formats/foo.md` ->
`ledgerkit/importers/foo.py`). More formats will be added there later.

Every importer module reads and writes its format, and exposes:

- `sniff(text: str) -> bool` -- True when the text looks like this format. A cheap check on the
  first lines, as each format file says.
- `parse(text: str) -> ImportResult` -- every transaction, in file order. A malformed record does not
  abort the import: it becomes a `Skipped` holding the 1-based line its record starts on and a
  reason, and parsing goes on. `FormatError` only when the text is not this format at all, or where
  the format file says so.
- `dump(transactions: list[Transaction], **options) -> str` -- the transactions written in the
  format, as the format file's "Writing" section says, options included. Reading back what `dump`
  wrote gives the same transactions, except for what that section says the format loses.

`ledgerkit/importers/__init__.py` exposes:

- `FORMATS: dict[str, ModuleType]` -- format name -> importer module, one entry per format file.
- `load(path: str | os.PathLike[str]) -> ImportResult` -- reads the file as UTF-8, falling back to
  cp1252 when it is not valid UTF-8; asks each importer's `sniff` in turn and parses with the first
  that says yes; raises `FormatError` when none does.

## Tests

Tests go in `tests/importers/`: one test file per format, and one for `load`. A format's tests
cover every section of its format file, reading and writing, each rule with its own test and each
edge case the section names (every date form, every mark, every malformed case), plus a round trip
through `dump` and `parse`. Sample files go in `tests/importers/data/<format>/`. The planted tests
in `tests/planted/` must keep passing.
