# nightly

The nightly database backup: dumps Postgres, compresses the dump and uploads it to object storage.
Cron runs `python3 -m nightly` at 02:00.

- Python 3.12, standard library only (the backup host has no pip).
- Tests: `python3 -m pytest -q`.
