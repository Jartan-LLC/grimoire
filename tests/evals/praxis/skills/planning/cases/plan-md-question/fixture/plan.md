# Plan: faster search

## Approach

Index product names in SQLite FTS5 instead of the `LIKE` scan in `shop/search.py`.

## Steps

1. Add an FTS5 table `products_fts` and fill it from `products` in a migration.
2. Point `search()` at it; keep the result order by rank.
3. Cache nothing: FTS5 answers in milliseconds on 40,000 rows.

## Verification

- `python3 -m pytest -q` -- the search tests pass on the new table.
