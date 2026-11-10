# stocktake

Counts the shop's stock from `stock.csv` every night and emails the manager the items
running low.

- Python 3.12, standard library only.
- Run the tests with `python3 -m pytest -q`.
- The nightly cron runs `python3 -m stocktake`.
