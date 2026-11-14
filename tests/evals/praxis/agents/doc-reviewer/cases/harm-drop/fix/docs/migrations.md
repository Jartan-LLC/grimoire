# Migrations

Run `db migrate` to apply pending migrations.

`db migrate --drop-unused` also drops every table the schema no longer names, with its data. This
cannot be undone: take a backup first.
