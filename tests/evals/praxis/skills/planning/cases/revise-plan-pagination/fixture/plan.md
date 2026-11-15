# Plan: nightly vendor import

## Approach

`GET /v1/products` returns the full catalogue; store it in `products`.

## Steps

1. `vendor/client.py`: `fetch_all()` calls `GET /v1/products` once.
2. `vendor/importer.py`: upsert every product by `sku`.
3. A cron entry runs the import at 02:00.

## Verification

- `python3 -m pytest -q` with a fake client returning three products.
