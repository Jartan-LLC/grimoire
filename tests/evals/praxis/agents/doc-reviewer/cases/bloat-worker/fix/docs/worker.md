# Run a worker

`jobq work` takes jobs from the queue and runs them, 8 at a time unless you pass `--concurrency N`.
Stop it with Ctrl-C.

A job with no payload is dropped with a log line. On SIGTERM the worker finishes its current job
first. MOVED replies from a Redis cluster are followed.
