# Commits per author

`gitstat authors` lists each author with their number of commits, most first. Add
`--after 2026-01-01` to count only commits after that date.

Mailmap entries whose emails differ only in case are merged. A shallow clone prints a warning and
counts only the commits it has. Commits with no author email count as `unknown`.
