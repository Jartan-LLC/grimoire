# contactkit

Reads contacts from three address-book formats into `Contact`s (contactkit/model.py). Each
format is a module under `contactkit/readers/` with one function,
`read(text: str) -> list[Contact]`:

- `vcard.py`: vCard 3.0 and 4.0; `FN`, `EMAIL` (the first one), `TEL` (the first one);
  folded lines unfolded.
- `csv.py`: the header `name,email,phone` in any column order; extra columns ignored.
- `ldif.py`: `cn`, `mail`, `telephoneNumber`; base64 values (`::`) decoded.

A record with no name is skipped. Each reader has its own tests in `tests/test_<format>.py`.
