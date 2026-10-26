I got two review comments on `parse_duration`:

1. `parse_duration("-5m")` silently returns 300. It should raise `ValueError` for a negative or malformed
   duration.
2. The local variable `secs` should be called `seconds`.

Make both changes, with a test for the first, and commit them.
