# Two more columns in the orders CSV export

Status: agreed (Priya, finance; Tom, backend), 2026-11-04.

`python3 -m export orders --month 2026-10` writes `orders-2026-10.csv`. Finance wants the
order's currency and, for refunded orders, when it was refunded.

## Behaviour

- Two new columns at the end, after `total`: `currency` (the order's three-letter code,
  such as `EUR`) and `refunded_at`.
- `refunded_at` is the refund time in UTC as `YYYY-MM-DDTHH:MM:SSZ`, and empty when the
  order was not refunded.
- The existing columns keep their names, order and formats.
- The only reader is finance's spreadsheet, which looks columns up by header name, so
  new columns at the end do not affect it.

The export ships on merge like everything else in this repository.
