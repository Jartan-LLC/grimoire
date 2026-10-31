# QIF (Quicken Interchange Format)

Exported by several banks as `.qif`. Plain text, one field per line; a line's first character is
its field code and the rest of the line is the value.

`sniff`: True when the first non-blank line starts with `!Type:`.

## Structure

- The first non-blank line is a type header: `!Type:Bank`, `!Type:CCard` or `!Type:Cash`. Any other
  type (for example `!Type:Invst`) raises `FormatError("unsupported QIF type: Invst")`.
- Then records, each ending with a line that is exactly `^`. A last record with no `^` before the end
  of the file is still a record. Blank lines are ignored.

## Fields

- `D` -- date. Accepted forms: `MM/DD/YYYY`, `MM/DD/YY`, and `M/D'YY` (an apostrophe before a
  two-digit year, written by older Quicken). `-` or `.` may stand in for `/`. Month and day may be
  one digit and may be padded with a space (`D 3/ 1'26`). A two-digit year YY means 20YY.
- `T` -- amount. `U` means the same; when a record has both, `T` wins. Amounts may carry thousands
  separators (`-1,234.56`) and may have no decimals (`-12`).
- `P` -- payee. `M` -- memo. `N` -- check number or reference, which becomes `ref`.
- `L` -- category. A category in square brackets (`L[Savings]`) is a transfer to another account:
  keep the transaction, with category `transfer:Savings`.
- `C` (cleared status) and `A` (address lines) are ignored, as is any field code not listed here.

## Splits

A record may be split across categories with repeated groups of `S` (split category), `E` (split
memo) and `$` (split amount) lines; each group starts at its `S` line. A record with splits gives one
`Transaction` per split instead of one for the record: same date, payee and ref; the amount from `$`;
the category from `S` (brackets mean a transfer, as for `L`); the memo from `E`, or the record's `M`
when the split has no `E`. When the split amounts do not add up to the record's amount, skip the
record with the reason "splits do not add up".

## Malformed records

A record needs a date and an amount; a missing payee is allowed (payee `""`). A record missing
either, or whose date or amount does not parse, is skipped; its line is the line of the record's
first field.

## Currency

QIF carries no currency: every transaction keeps the model's default currency.

## Example

```text
!Type:Bank
D03/01/2026
T-3.50
PCafe Uno
LEating out
^
D3/ 4'26
T-120.00
PGreen Market
MWeekly shop
SGroceries
$-100.00
SHousehold
EBin bags
$-20.00
^
```

## Writing

`dump(transactions, type="Bank")` writes the header `!Type:<type>` (`Bank`, `CCard` or `Cash`;
anything else raises `FormatError`), then one record per transaction, in order, each ending with
`^`:

- `D` in `MM/DD/YYYY`; `T` with two decimals and no thousands separators (`-1234.50`);
- `P` always, even when empty; `M` only when the memo is not empty; `N` only when there is a ref;
- `L` only when there is a category, a `transfer:X` category written `L[X]`.

A payee, memo, ref or category containing a line break raises `FormatError`. Writing never makes
splits: each transaction is its own record. The format loses the currency (read back as the model's
default) and nothing else.
