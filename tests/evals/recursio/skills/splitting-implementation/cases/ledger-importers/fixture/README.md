# ledger

Reads bank statements into one list of transactions.

## Model

`ledger.Transaction` (in `src/ledger/model.py`) is the record every importer produces.

## Planned

- `ledger.importers.csv_bank`: the bank's CSV export -- semicolon-separated, `dd.mm.yyyy` dates,
  comma as the decimal separator, header row `Datum;Betrag;Empfaenger;Verwendungszweck`.
- `ledger.importers.ofx`: OFX 1.x SGML files -- `<STMTTRN>` blocks with `DTPOSTED`, `TRNAMT`,
  `NAME` and `MEMO`; tags are not always closed.
- `ledger.importers.qif`: QIF bank files -- `D` (date), `T` (amount), `P` (payee), `M` (memo)
  lines, `^` ends a record.
- `ledger summary FILE...`: money in and out per month across all the files, the importer
  picked by each file's extension.
