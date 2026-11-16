# Review: CSV export for finance

Reviewer: Dana

1. `reports/export.py`, `export_csv`: if `format_row` raises partway through, `out` is never
   closed. On the Windows build agents the half-written file then stays locked, and the
   rerun can't overwrite it.

2. `format_row`: the docstring says the amount is in cents, but these are euros.

3. Nit: `HEADER` could be a tuple, since nothing changes it. Your call.
