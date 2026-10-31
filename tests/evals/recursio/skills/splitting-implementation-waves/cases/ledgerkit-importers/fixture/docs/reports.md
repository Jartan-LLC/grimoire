# Reports

`ledgerkit/reports.py`: pure functions over an iterable of `Transaction`s.

- `MonthTotals` -- a frozen dataclass with `income`, `spending` and `net`, all `Decimal`. Spending
  is money out written as a positive number; `net = income - spending`.
- `monthly_totals(txs) -> dict[str, MonthTotals]` -- keyed `"YYYY-MM"`, in calendar order. Months
  with no transactions between the first and the last month are included, with zeros.
- `by_category(txs, month: str | None = None) -> list[tuple[str, Decimal]]` -- spending per
  category (positive), for one month (`"YYYY-MM"`) or for all transactions. Category `None` counts
  as `"uncategorized"`. Transfers (a category starting `transfer:`) and money in are left out.
  Sorted by amount, largest first, then by category name.
- `render_text(txs) -> str` -- the monthly totals as a fixed-width table, one line per month after
  a header line. Each line is the month left-aligned in seven characters, then income, spending and
  net, each right-aligned in ten characters with two decimals, the four cells separated by one
  space; the header's cells are `Month`, `Income`, `Spending` and `Net`. Lines end with `\n`.

Every function raises `ValueError` when the transactions are in more than one currency; no
transactions give an empty result (`render_text` gives the header alone).

Tests go in `tests/test_reports.py`.
