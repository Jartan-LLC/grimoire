# Paginate GET /internal/orders

Status: agreed (Mira, Tom), 2026-11-03.

`GET /internal/orders` returns every order in one response, now about 180,000 rows, and the
admin CLI times out reading it. Only `tools/admin_cli.py` in this repo calls the endpoint:
the access logs for October show no other client, and the endpoint is reachable only
inside the VPN.

## Behaviour

- Query parameters `limit` (default 50, at most 200) and `cursor` (optional).
- Orders come in ascending `id` order.
- The response is `{"orders": [...], "next_cursor": <string or null>}`. `next_cursor` is
  the last returned order's id, as a string; it is null on the last page.
- A `limit` above 200, below 1 or not a whole number, or a `cursor` that is not a whole
  number, gives a 400 with `{"error": "<reason>"}`.
- `tools/admin_cli.py export-orders` follows `next_cursor` until it is null and writes
  every order, as it does now.

The service and the CLI ship together from this repo, so they change in one PR. No other
endpoint changes.
