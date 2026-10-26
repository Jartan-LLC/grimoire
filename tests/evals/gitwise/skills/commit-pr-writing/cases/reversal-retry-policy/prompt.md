On this branch, failed webhook deliveries are retried immediately, three times, and the receiving side
is getting hammered. Change it to wait 1, 2 and 4 seconds between the three retries (take `sleep` as a
parameter so the test stays fast), keep the tests passing, and commit. The branch is already pushed.
