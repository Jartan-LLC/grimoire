# invoicekit

Issues VAT invoices for a small EU seller, numbers them without gaps, converts currencies, and
works out reminders and late-payment interest, as a library and a command. No npm dependencies.

## Contract

`src/types.js` holds what the modules pass to one another: `Money`, `Party`, `Line`, `Invoice`,
`TaxCategory` and the other JSDoc typedefs, `InvoiceError`, and the constants `CURRENCY_DIGITS`
and `TAX_CATEGORIES`. Money is always an integer count of minor units; no module computes money
in floating point. Each module below uses only the contract and nothing of its siblings; only the
command uses them all. Every module throws `InvoiceError` for input it refuses.

## VAT (`src/tax.js`)

Rates, in percent, as our accountant gave them. A rate is held in basis points (19 % is 1900,
5.5 % is 550) so that every sum stays an integer.

| Country | Standard | Reduced | Super-reduced |
|---------|----------|---------|---------------|
| AT | 20 | 10 | - |
| BE | 21 | 6 | - |
| DE | 19 | 7 | - |
| DK | 25 | - | - |
| ES | 21 | 10 | 4 |
| FR | 20 | 5.5 | 2.1 |
| IE | 23 | 13.5 | 4.8 |
| IT | 22 | 10 | 4 |
| LU | 17 | 8 | 3 |
| NL | 21 | 9 | - |
| PL | 23 | 8 | - |
| SE | 25 | 12 | 6 |

- `rateFor(country, category)`: the rate in basis points. `zero` and `exempt` are 0. A category
  the country lacks (`reduced` in DK), or a country not in the table, throws.
- `validVatId(vatId, country)`: a format check only. Spaces, dots and hyphens are removed and
  letters upper-cased; the id must start with the country code (Greece writes `EL`) and then match:
  DE 9 digits; AT `U` and 8 digits; BE 10 digits starting with 0 or 1; NL 9 digits, `B`, 2 digits;
  IT 11 digits; FR 2 digits or letters (not O or I) then 9 digits; ES a letter or digit, 7 digits,
  a letter or digit; every other country 8 to 12 letters or digits.
- `treatment(seller, buyer, { ossRegistered = false, crossBorderB2CYearToDate = 0 })`: how the
  sale is taxed, as `{ scheme, rateCountry, note }`. The seller must be in the table and have a
  valid VAT id.
  - Same country: `domestic`, seller's rates, no note.
  - Buyer in another table country, a business with a valid VAT id: `reverse-charge`, every line
    at 0, note `Reverse charge: VAT to be accounted for by the recipient (Article 196, Directive
    2006/112/EC). Customer VAT ID: <id>`.
  - Buyer in another table country, a consumer or a business without a valid VAT id: `oss` with
    the buyer's country's rates when `ossRegistered` is true or the seller's cross-border B2C sales
    this calendar year (`crossBorderB2CYearToDate`, EUR minor units) exceed EUR 10,000.00;
    otherwise `domestic` with the seller's rates.
  - Buyer outside the table: `export`, every line at 0, note `Export outside the EU, exempt from
    VAT (Article 146, Directive 2006/112/EC).`
- `computeTax(invoice, { rounding = "line", ...treatmentOptions })`: returns `{ lines, byRate,
  net, vat, gross, notes }`, all amounts as `Money`.
  - A line's net is `quantity x unitPrice x (1 - discountPct / 100)`, rounded once, half up (away
    from zero), to the minor unit: 1.5 x EUR 85.00 less 10 % is EUR 114.75.
  - `rounding: "line"` rounds each line's VAT, `net x rate / 10000` half up, and sums them per
    rate. `rounding: "total"` sums the nets per rate and rounds the VAT of each sum once. Three
    lines of EUR 0.10 at 25 % give EUR 0.09 by line (3 cents each) and EUR 0.08 by total.
  - `byRate` lists `{ rate, net, vat }` for each rate used, highest rate first. `gross` is net
    plus VAT.
  - An `exempt` line adds the note `VAT exempt supply (Article 132, Directive 2006/112/EC).`, once
    per invoice. Notes keep the invoice's own notes first, then the treatment's, then exemptions.
  - A line whose currency differs from the invoice's, a quantity with more than three decimals, or
    a discount outside 0 to 100 throws. Credit notes carry negative quantities and work the same.

## Currency (`src/currency.js`)

- `parseRatesCsv(text)`: reference rates in the ECB's CSV layout, a header `Date,USD,JPY,...` and
  rows such as `2026-10-29,1.0850,162.34,...`, each the units of that currency per 1 EUR. `N/A`
  or an empty cell is no rate; blank lines and a trailing comma are fine. A malformed date or
  number throws with its line number. Returns a rate table; rates stay decimal strings.
- `rateOn(table, currency, date)`: the latest rate on or before `date` (a Saturday uses Friday's).
  EUR is always 1. No rate on or before the date throws `no USD rate on or before 2026-01-01`.
- `convert(money, currency, date, table, { rounding = "half-even" })`: triangulates through EUR,
  `amount x rate(to) / rate(from)`, adjusted for the two currencies' minor-unit digits, and rounds
  once at the end, never at the EUR step. Work in `BigInt` or scaled integers. USD 100.00 at USD
  1.0850 and JPY 162.34 is JPY 14962; EUR 10.00 at BHD 0.4093 is BHD 4.093. The same currency
  comes back unchanged.
- `roundDiv(numerator, denominator, mode)` on `BigInt`: `half-even` takes 2.5 to 2, 3.5 to 4 and
  -2.5 to -2; `half-up` rounds halves away from zero, 2.5 to 3 and -2.5 to -3. EUR 0.50 at JPY 161
  is JPY 80 half-even and JPY 81 half-up.
- `parseMoney(text, currency)`: `"1,234.5"` in EUR is 123450 minor units. More decimals than the
  currency has (`"1.234"` in EUR, `"1.5"` in JPY) throws, and so does a currency missing from
  `CURRENCY_DIGITS`.
- `formatMoney(money)`: `EUR 1,234.50`, `JPY 14,962`, `BHD 4.093`, `-EUR 12.00`.

## Numbering (`src/numbering.js`)

A series turns a date and a counter into an invoice number. `createSeries({ id, format, reset,
start = 1, kind = "invoice" })` validates the definition:

- Tokens: `{YYYY}`, `{YY}`, `{MM}`, `{seq}` (no padding) and `{seq:N}` (zero-padded to N digits;
  a longer number is not cut). `{{` and `}}` are literal braces. An unknown token throws, and so
  does a format without exactly one seq token.
- `reset` is `never`, `yearly` or `monthly`. A yearly series needs `{YYYY}` or `{YY}` in its
  format, a monthly one a year token and `{MM}`, or numbers would repeat; otherwise it throws.
- The defaults the command uses: `INV` with `INV-{YYYY}-{seq:5}`, yearly, and the credit-note
  series `CN` with `CN-{YYYY}-{seq:4}`, yearly, `kind: "credit-note"`.

`createNumberer(store, series)` returns an object with:

- `next(seriesId, date, { credits } = {})`: the next number for the date's period (`2026` yearly,
  `2026-10` monthly, `all` never), recorded as issued. A new period starts at `start`. A date
  earlier than the last number issued in the series throws `2026-10-01 is before INV-2026-00041
  (2026-10-05)`. A credit-note series requires `credits`, the number of an issued, not voided
  invoice in an invoice series, or throws.
- `void(seriesId, number, reason, date)`: marks an issued number void. The number stays used and is
  never issued again; voiding an unknown or already void number throws.
- `log(seriesId)`: every number in order as `{ number, period, seq, date, status, reason?,
  credits? }`, `status` being `issued` or `void`.
- `audit(seriesId)`: the problems in a store edited by hand: a missing seq in a period, a seq used
  twice, dates out of order, as messages; `[]` when clean.

The store is injected: any object with `get(key)` returning a string or `undefined` and
`set(key, value)`. Counters live at `series/<id>/<period>` and the log at `series/<id>/log`, as
JSON. `memoryStore()` keeps them in a `Map`; `fileStore(path)` keeps them in one JSON file and
writes it to a temporary file in the same directory, then renames it over the old one.

## Dunning (`src/dunning.js`)

The ledger is a list of issued invoices (`{ number, buyer, issueDate, dueDate, gross: Money,
reminders: [{ level, date }] }`) and payments (`{ date, buyer, amount: Money }`), dates as
`YYYY-MM-DD`.

- `daysOverdue(dueDate, asOf)`: whole calendar days after the due date, 0 when not overdue.
- Default schedule, which a caller may replace: level 1 at 7 days overdue, `Payment reminder`, no
  fee; level 2 at 21 days, `Second reminder`, fee 5.00; level 3 at 35 days, `Final notice`, fee
  10.00. Fees are in the invoice's currency, 5 and 10 whole units of it (EUR 5.00, BHD 5.000),
  except in JPY, which charges JPY 500 and JPY 1,000.
- `interest(principalChanges, dueDate, asOf, baseRates, { marginPct = 8 })`: statutory interest at
  the base rate plus 8 percentage points a year, simple, actual/365 (leap years too). It runs from
  the day after the due date through `asOf`, each day at the rate in force that day on the balance
  outstanding that day, summed exactly and rounded half up once at the end. `baseRates` is a list
  of `{ from, ratePct }` (decimal strings, negative allowed, as `"-0.88"`), changing on 1 January
  and 1 July. EUR 1,000.00 due 2026-03-31, unpaid through 2026-04-30 with a base rate of 1.27, is
  30 days at 9.27 %: EUR 7.62.
- `allocate(ledger, asOf, options)`: applies each buyer's payments, in date order, to their open
  invoices oldest due date first (then by number): to that invoice's reminder fees first, then
  interest accrued to the payment date, then principal. What is left after every invoice is paid
  is the buyer's credit. Returns each invoice's outstanding principal, fees and interest as of
  `asOf`, and each buyer's credit.
- `remindersDue(ledger, asOf, { schedule, baseRates })`: for each invoice still open, the highest
  level its days overdue reach, if not already sent; one reminder per invoice per run, so a level
  skipped while unpaid is not sent late. Each is `{ number, buyer, level, title, daysOverdue,
  principal, fees, interest, total }`, the fees including this reminder's own. Sorted by days
  overdue, most first, then number.

## Command (`bin/invoicekit.js`)

- `invoicekit issue [--store FILE] [--series ID] [--rounding line|total] [--oss] [--b2c-ytd
  AMOUNT] [--rates FILE --currency CODE] [--json] INVOICE.json` reads an invoice with `number:
  null`, takes the next number from the series (default `INV`, or `CN` for a credit note) for its
  issue date, computes the tax, and prints the invoice: number, dates, seller and buyer with VAT
  ids, a line table (description, quantity, unit price, net, rate), VAT by rate, net, VAT and gross
  totals, and the notes. With `--currency` it adds the gross converted at the issue date's rate.
  `--json` prints the completed invoice and its tax as JSON instead. The store defaults to
  `.invoicekit/numbers.json`.
- `invoicekit remind --as-of DATE [--base-rates FILE] [--record] LEDGER.json` prints one block per
  reminder due: title, invoice number, days overdue, and principal, fees, interest and total as
  money. `--record` writes the reminders into the ledger's invoices. `--base-rates` is a CSV of
  `from,ratePct` rows; without it the base rate is 0.

An `InvoiceError` prints `invoicekit: message` to stderr and exits 1; nothing is recorded. A usage
error or a file that cannot be read or parsed as JSON prints a message and exits 2.

## Status

Only the contract exists. Each module gets its own test file in `test/`.
