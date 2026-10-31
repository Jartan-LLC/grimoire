# Formats

`subkit/formats/` holds one module per subtitle format. Each format is specified in its own file
under `docs/formats/`; the file's name is the module's name (`docs/formats/foo.md` ->
`subkit/formats/foo.py`). More formats will be added there later.

Every format module reads and writes its format, and exposes:

- `sniff(text: str) -> bool` -- True when the text looks like this format. A cheap check on the
  first lines, as each format file says.
- `parse(text: str) -> ParseResult` -- every cue, in file order. A byte order mark at the start and
  `\r\n` line ends are accepted. A malformed record does not abort the parse: it becomes a
  `Skipped` holding the 1-based line its record starts on and a reason, and parsing goes on.
  `FormatError` only when the text is not this format at all, or where the format file says so.
- `dump(cues: list[Cue], **options) -> str` -- the cues written in the format, as the format file's
  "Writing" section says, options included. Reading back what `dump` wrote gives the same cues,
  except for what that section says the format loses.

`subkit/formats/__init__.py` exposes:

- `FORMATS: dict[str, ModuleType]` -- format name -> format module, one entry per format file.
- `load(path: str | os.PathLike[str]) -> ParseResult` -- reads the file as UTF-8, falling back to
  cp1252 when it is not valid UTF-8; asks each format's `sniff` in turn and parses with the first
  that says yes; raises `FormatError` when none does.
- `convert(text: str, to: str, **options) -> str` -- parses `text` with the first format whose
  `sniff` says yes and dumps its cues with format `to`, passing `options` on; an unknown `to`
  raises `FormatError`.

## Tests

Tests go in `tests/formats/`: one test file per format, and one for `load` and `convert`. A format's
tests cover every section of its format file, reading and writing, each rule with its own test and
each edge case the section names (every time form, every tag, every malformed case), plus a round
trip through `dump` and `parse`. Sample files go in `tests/formats/data/<format>/`. The planted
tests in `tests/planted/` must keep passing.
