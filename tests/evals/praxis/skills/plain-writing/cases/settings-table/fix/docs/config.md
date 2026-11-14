# Configuration

Set these in `queue.toml`.

| Setting | Default | What it sets |
|---|---|---|
| `workers` | 4 | Worker processes |
| `retry_limit` | 5 | Attempts before a job fails |
| `lock_timeout` | 30 | Seconds to wait for the queue lock; raise it on slow network disks |
| `fsync_every` | 0 | Fsync the journal every N jobs; 0 leaves it to the OS |
