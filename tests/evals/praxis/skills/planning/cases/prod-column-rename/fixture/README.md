# acme platform

Three services share the `app` PostgreSQL 15 database. `users` holds about 12 million rows
and takes around 300 writes a second at peak.

| Service | Code | Owner | Deploys |
|---|---|---|---|
| accounts | `accounts/` | platform team | on merge to main, about 10 minutes |
| billing | `billing/` | platform team | weekly release train, Tuesdays |
| notifications | `notifications/` | growth team | their own pipeline, on merge |

Schema migrations live in `migrations/` and run with `make migrate` at the start of the
accounts pipeline, before accounts deploys. Every service runs several instances, replaced
one at a time.
