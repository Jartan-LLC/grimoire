# ledgerkit

A small personal-finance library: transactions in, reports out. Money out is a negative
`amount`, money in a positive one. Amounts are `decimal.Decimal`, never floats.

The shared types are in `ledgerkit/model.py`; specs for each feature are under `docs/`.

## Development

Python 3.11 or later, standard library only; the tests need pytest.

    python3 -m pytest
