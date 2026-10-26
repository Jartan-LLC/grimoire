Issue #310: `parse_date("2026-02-30")` returns March 2nd instead of raising. Make it raise ValueError for
an impossible date, with a test, and commit. The old rows already stored with rolled-over dates need a
data migration; that's #311 and has to be scheduled with ops, so not in this change.
