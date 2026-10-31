# OFX (Open Financial Exchange)

Banks export OFX as `.ofx` or `.qfx`. Two versions exist in the wild, and the importer reads both:

- **OFX 1.x (SGML)**: a header of `KEY:VALUE` lines (`OFXHEADER:100`, `DATA:OFXSGML`,
  `VERSION:102`, ...), a blank line, then SGML. Leaf elements are not closed: a leaf's value runs to
  the next `<` (`<TRNAMT>-3.50`). Aggregates such as `<STMTTRN>` ... `</STMTTRN>` are closed. Elements
  usually sit one per line, but several may share a line.
- **OFX 2.x (XML)**: an `<?xml ...?>` declaration and an `<?OFX OFXHEADER="200" ...?>` processing
  instruction, then well-formed XML in which every element is closed: `<TRNAMT>-3.50</TRNAMT>`.

`sniff`: True when the first non-blank line starts with `OFXHEADER:`, or `<?OFX` appears in the
first five lines.

## What to read

Each `<STMTTRN>` aggregate is one transaction, whether it sits in a bank statement (`<STMTRS>`) or a
credit-card statement (`<CCSTMTRS>`):

- `DTPOSTED` -> `day`. Form `YYYYMMDD`, optionally followed by `HHMMSS`, then optionally `.XXX`
  milliseconds, then optionally a time zone in brackets (`[-5:EST]`, `[+1]`). Only the date counts.
- `TRNAMT` -> `amount`, signed. Most banks write a decimal point; some write a decimal comma
  (`-3,50`), which means the same.
- `NAME` -> `payee`. When there is no `NAME`, use the `<NAME>` inside a `<PAYEE>` aggregate; when
  there is neither, the payee is `""`.
- `MEMO` -> `memo`. `FITID` -> `ref`. `TRNTYPE` and every other element are ignored.
- Currency: the `<CURDEF>` of the enclosing statement. A transaction's own `<CURRENCY><CURSYM>`
  overrides it.
- Text values have surrounding whitespace trimmed and the entities `&amp;`, `&lt;` and `&gt;`
  decoded.

A file may hold several statements (several `<STMTRS>` in one response, possibly in different
currencies): read them all, in file order.

## Duplicates

Banks repeat transactions across overlapping downloads. Within one file, a `<STMTTRN>` whose `FITID`
was already seen is skipped with the reason `duplicate FITID <id>`.

## Malformed

A `<STMTTRN>` with no `DTPOSTED` or no `TRNAMT`, or with one that does not parse, is skipped; its line
is the line its `<STMTTRN>` opens on. A text with no `<OFX>` element at all raises `FormatError`.

## Example (1.x)

```text
OFXHEADER:100
DATA:OFXSGML
VERSION:102

<OFX>
<BANKMSGSRSV1><STMTTRNRS><STMTRS>
<CURDEF>EUR
<BANKTRANLIST>
<STMTTRN>
<TRNTYPE>DEBIT
<DTPOSTED>20260301120000.000[+1:CET]
<TRNAMT>-3.50
<FITID>20260301-1
<NAME>Cafe Uno
</STMTTRN>
</BANKTRANLIST>
</STMTRS></STMTTRNRS></BANKMSGSRSV1>
</OFX>
```

## Writing

`dump(transactions, account="0000")` writes OFX 2.x: the `<?xml version="1.0" encoding="UTF-8"?>`
declaration, the line `<?OFX OFXHEADER="200" VERSION="220" SECURITY="NONE" OLDFILEUID="NONE"
NEWFILEUID="NONE"?>`, then `<OFX><BANKMSGSRSV1>` holding one `<STMTTRNRS><STMTRS>` per currency, in the
order each currency first appears. Each statement has its `<CURDEF>`, a `<BANKACCTFROM>` with
`<ACCTID>` set to `account`, and a `<BANKTRANLIST>` with a `<DTSTART>` and `<DTEND>` (the first and
last day of its transactions, `YYYYMMDD`) and one `<STMTTRN>` per transaction, in order:

- `<TRNTYPE>` is `CREDIT` for an amount of 0 or more, else `DEBIT`;
- `<DTPOSTED>` `YYYYMMDD`; `<TRNAMT>` signed, two decimals, a decimal point;
- `<FITID>` the ref; a transaction with no ref gets `<day>-<n>`, the day as `YYYYMMDD` and n
  counting from 1 within that day (`20260301-2`);
- `<NAME>` the payee, cut to its first 32 characters; `<MEMO>` only when the memo is not empty;
- text with `&`, `<` and `>` written as entities. Every element is closed, one per line,
  indented two spaces per level.

Two transactions with the same ref raise `FormatError`, since the second would read back as a
duplicate. The format loses the category, a payee's characters past the 32nd, and a missing ref
(read back as the generated FITID).
