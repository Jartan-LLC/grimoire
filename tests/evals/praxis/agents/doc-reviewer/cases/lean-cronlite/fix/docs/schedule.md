# Schedule jobs

Add a job with `cronlite add "0 9 * * 1" ./report.sh`; the schedule is a five-field cron
expression in local time. `cronlite list` shows each job with its ID, and `cronlite remove ID`
removes one.
