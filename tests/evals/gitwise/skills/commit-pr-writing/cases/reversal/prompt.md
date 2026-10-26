The price cache on this branch has to survive restarts, and the in-memory dict doesn't. Switch it to a JSON
file at `.cache/prices.json` (create the directory if needed), keep the test passing, and commit. The branch
is already pushed.
