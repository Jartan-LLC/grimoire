# Wait for a service to start

In a start script, run `portwait db:5432` before the step that needs the database. It returns
once `db:5432` accepts a connection, or exits 1 after 60 seconds. Pass `--timeout SECONDS` to wait
longer.
