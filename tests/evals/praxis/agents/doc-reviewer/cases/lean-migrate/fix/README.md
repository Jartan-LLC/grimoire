# notes

A small notes app. `python3 -m notes` starts the dev server on port 8000; it keeps the notes in
`data/app.db`.

## Database migrations

Stop the dev server first. Then run `python3 scripts/migrate.py`: it copies `data/app.db` to
`data/app.db.before` and applies, in order, each new `.sql` file in `migrations/`. To undo a run,
copy `data/app.db.before` back over `data/app.db`.
