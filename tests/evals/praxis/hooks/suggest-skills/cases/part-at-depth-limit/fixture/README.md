# exportkit

Writes a list of `Record`s (exportkit/model.py) out in three formats, each a module under
`exportkit/formats/` with one function, `dump(records: list[Record]) -> str`:

- `csv.py`: a header row `id,name,amount`, then one row per record; amounts with two
  decimals; fields holding a comma or a quote are quoted as RFC 4180 says.
- `json.py`: a JSON array of objects with the keys `id`, `name`, `amount`, in that order;
  amounts as strings with two decimals.
- `xml.py`: `<records>` holding one `<record id="...">` per record with `<name>` and
  `<amount>` children; text escaped.

Each format has its own tests in `tests/test_<format>.py`.
