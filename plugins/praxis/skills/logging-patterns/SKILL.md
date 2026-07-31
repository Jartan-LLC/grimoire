---
name: logging-patterns
description: Logging conventions -- level usage, formatting style, structured output.
when_to_use: Writing code that logs events, configuring log output, or choosing log levels.
user-invocable: false
---

# Logging Conventions

## Setup

One logger per module, at module level:

```python
import logging

logger = logging.getLogger(__name__)
```

## Formatting

Use `%s`-style formatting arguments, not f-strings -- the message template is preserved for structured aggregator queries:

```python
logger.info("Cleaned up %d expired sessions", count)  # yes
logger.exception("SMTP send failed for %s", email)    # yes (in an except handler)
logger.info(f"Cleaned up {count} expired sessions")   # no
```

`%s` deferral is stdlib-specific -- `structlog` uses kwargs, not `%s`. See `pythonica:python-observability`.

## Level Conventions

| Level | Use for |
|---|---|
| `DEBUG` | Cache hit/miss, slow-path internals (opt-in only) |
| `INFO` | Startup/shutdown, admin bootstrap, cleanup counts, rate limit hits |
| `WARNING` | Recoverable anomalies, swallowed exceptions, degraded operation |
| `ERROR` | Unexpected exceptions on operational paths -- use `logger.exception(...)` |
| `CRITICAL` | Reserved for unusable state |

## Output

Log to **stderr** when stdout carries the program's own output -- the common case: CLIs, filters, pipeline stages (also Python's `logging.StreamHandler` default). Use **stdout** only for pure log-shipping services that emit nothing else. One record per line either way. Container runtimes (Docker, k8s) capture both streams, so the choice isolates logs from program output, not runtime visibility -- no file sinks or log rotation in-app.

Support two formats via config:
- **`plain`** -- Readable for local dev
- **`json`** -- Stable single-line object per record for log aggregators (Loki, Datadog, ELK, CloudWatch)

Timestamps in UTC in both formats.
