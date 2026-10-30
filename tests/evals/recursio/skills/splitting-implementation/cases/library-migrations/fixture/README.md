# catalog

The branch library's catalogue: books, members and loans in SQLite. The schema is built by the
numbered migrations in `src/catalog/migrations/`, which `catalog.migrate` runs in order.

Members belong to a tier (`standard`, `student` or `staff`); each tier sets how many days a loan
lasts. Dates are stored as ISO `YYYY-MM-DD` text.
