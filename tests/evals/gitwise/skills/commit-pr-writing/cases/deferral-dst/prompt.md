Issue #31: `to_utc("2026-03-01 09:00", "Europe/Paris")` returns 09:00 UTC; it ignores the offset entirely.
Fix it with a test and commit. Times that fall inside a daylight-saving jump are a separate, harder
problem tracked in #32, so leave those alone.
