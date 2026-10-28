# pingmon

Checks that a list of URLs answer, and alerts when one stops.

## Configure

Write `pingmon.toml`:

```toml
[[check]]
url = "https://example.com/health"
interval_s = 60
timeout = 5
retries = 2
```

Then run `python3 -m pingmon pingmon.toml`.
