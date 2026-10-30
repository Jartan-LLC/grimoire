# kvs

A key-value store interface (`kvs.base.Store`) with interchangeable backends.

## Backends

- `memory` (`src/kvs/memory.py`): done.
- `sqlite`: one table `kv(key TEXT PRIMARY KEY, value BLOB, expires REAL)`; expired keys read as
  missing and are purged on `set`.
- `jsonfile`: the whole store in one JSON file, written atomically (temp file, then rename); values
  are bytes, stored base64.
- `sharded`: spreads keys over N child stores by a stable hash of the key; `keys()` merges the
  children's.

## Command

`kvs --backend sqlite|jsonfile --path P get|set|delete|keys [KEY] [VALUE] [--ttl SECONDS]`.
