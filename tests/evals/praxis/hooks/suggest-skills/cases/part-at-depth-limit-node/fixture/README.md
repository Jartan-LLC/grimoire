# unitparse

Parses quantities with units. Each parser is a module under `src/parsers/` exporting
`parse(text)`, which returns `{ value, unit }` or throws a `ParseError` from
`src/errors.js`:

- `length.js`: `mm`, `cm`, `m`, `km`, `in`, `ft`; the value in metres.
- `mass.js`: `mg`, `g`, `kg`, `t`, `oz`, `lb`; the value in kilograms.
- `duration.js`: `ms`, `s`, `min`, `h`, `d`, and compound forms like `1h30min`; the value in
  seconds.

Each parser has its own tests in `test/<name>.test.js`, run with `node --test`.
