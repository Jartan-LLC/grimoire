# CAMT.053 (ISO 20022 bank-to-customer statement)

The XML statement that SEPA banks are moving to, exported as `.xml`. Read it with the standard
library's XML parser; match elements by their local name, ignoring the namespace, since banks send
versions `camt.053.001.02` to `camt.053.001.08` and the element names below hold across them
except where noted.

`sniff`: True when the text's first 1,000 characters contain
`urn:iso:std:iso:20022:tech:xsd:camt.053.`.

Text that is not well-formed XML raises `FormatError("not well-formed XML: <parser message>")`.

## Statements and entries

The document holds one or more `<Stmt>` elements; read them all, in order. Each `<Ntry>` (entry)
inside a statement gives one transaction, or several for a batch (below). An entry's line is the
line its `<Ntry>` start tag is on (the parser can report it; counting from 1).

- **Amount**: `<Amt Ccy="EUR">12.50</Amt>`, a child of `<Ntry>`, always positive. `<CdtDbtInd>`
  gives the sign: `CRDT` positive, `DBIT` negative. When `<RvslInd>` is `true`, the entry reverses
  an earlier one: flip the sign.
- **Currency**: the `Ccy` attribute of the entry's `<Amt>`.
- **Status**: `<Sts>` holds the code directly (`<Sts>BOOK</Sts>`, up to version 05) or in a `<Cd>`
  child (`<Sts><Cd>BOOK</Cd></Sts>`, version 06 on). Only `BOOK` entries are transactions; a
  `PDNG` (pending) or `INFO` entry is skipped with the reason `pending` or `info`.
- **Day**: `<BookgDt>` holding `<Dt>` (`YYYY-MM-DD`) or `<DtTm>` (ISO 8601 date-time, only the date
  counts); when `<BookgDt>` is missing, `<ValDt>` in the same forms.
- **Ref**: the `<EndToEndId>` under the entry's `<TxDtls><Refs>`, unless it is `NOTPROVIDED`; then
  the entry's own `<AcctSvcrRef>`; else None.

## Payee and memo

Taken from the entry's `<TxDtls>` (the first one, or each one for a batch):

- **Payee**: the other party. For money out (`DBIT`, before any reversal) it is the creditor,
  for money in the debtor: `<RltdPties><Cdtr><Nm>` or `<RltdPties><Dbtr><Nm>` up to version 07, and
  from version 08 `<RltdPties><Cdtr><Pty><Nm>` (or `<Dbtr><Pty><Nm>`). None found: `""`.
- **Memo**: the `<Ustrd>` lines of `<RmtInf>`, joined with one space; when there are none, the
  entry's `<AddtlNtryInf>`; else `""`.

## Batches

An entry whose `<NtryDtls>` holds two or more `<TxDtls>`, each with its own amount, is a batch
booking: it gives one transaction per `<TxDtls>`, in order, each with the entry's day, currency and
sign, its own amount, payee, memo and ref (its own `<EndToEndId>`, then the entry's
`<AcctSvcrRef>`). A `<TxDtls>` amount is `<AmtDtls><TxAmt><Amt>` up to version 07 and `<Amt>`
directly under `<TxDtls>` from version 08. When the amounts do not add up to the entry's amount,
the entry is skipped with the reason `batch does not add up`. `<TxDtls>` without amounts are not a
batch: the entry gives one transaction from the first of them.

## Malformed

An entry with no `<Amt>`, no `<CdtDbtInd>` or no day, or one whose amount or date does not parse,
is skipped with a reason naming what is wrong (`missing amount`, `bad date 2026-02-30`).

## Example (version 02)

```text
<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.02">
  <BkToCstmrStmt>
    <Stmt>
      <Ntry>
        <Amt Ccy="EUR">3.50</Amt>
        <CdtDbtInd>DBIT</CdtDbtInd>
        <Sts>BOOK</Sts>
        <BookgDt><Dt>2026-03-01</Dt></BookgDt>
        <AcctSvcrRef>BK-1</AcctSvcrRef>
        <NtryDtls><TxDtls>
          <Refs><EndToEndId>NOTPROVIDED</EndToEndId></Refs>
          <RltdPties><Cdtr><Nm>Cafe Uno</Nm></Cdtr></RltdPties>
          <RmtInf><Ustrd>Coffee</Ustrd><Ustrd>morning</Ustrd></RmtInf>
        </TxDtls></NtryDtls>
      </Ntry>
    </Stmt>
  </BkToCstmrStmt>
</Document>
```

## Writing

`dump(transactions, iban="", statement_id="LEDGERKIT")` writes version 08 (namespace
`urn:iso:std:iso:20022:tech:xsd:camt.053.001.08`), indented two spaces per level, with one
`<Stmt>` holding `<Id>` set to `statement_id`, `<Acct><Id><IBAN>` set to `iban`, and one `<Ntry>`
per transaction, in order: `<Amt Ccy=...>` the absolute amount with two decimals, `<CdtDbtInd>`
(`CRDT` for 0 or more), `<Sts><Cd>BOOK</Cd></Sts>`, `<BookgDt><Dt>`, and one `<TxDtls>` with
`<Refs><EndToEndId>` (the ref, or `NOTPROVIDED`), the payee as `<Cdtr><Pty><Nm>` for money out or
`<Dbtr><Pty><Nm>` for money in (left out when empty), and the memo as one `<Ustrd>` (left out when
empty). Text is escaped as XML requires. The format loses the category; a memo with line breaks
reads back with them as written.
