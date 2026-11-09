# reportkit

Renders a `Table` (reportkit/model.py) in three formats, each a module under
`reportkit/formats/` with one function, `render(table: Table) -> str`:

- `text.py`: columns padded to their widest cell, separated by two spaces, a row of `-`
  under the header; numbers right-aligned, text left-aligned.
- `csv.py`: RFC 4180 CSV with the header first; `None` cells empty.
- `markdown.py`: a GitHub table; `|` in a cell escaped as `\|`; numeric columns
  right-aligned with `---:`.

Each format has its own tests in `tests/test_<format>.py`.
