# stashd

Backs up a directory to a storage URL on a schedule. Reads its settings from `stashd.json`.

Each config carries a `version`. `loadConfig` runs the config through the migrations in
`src/migrations/` to bring an older file up to the current shape, so old files keep working.
