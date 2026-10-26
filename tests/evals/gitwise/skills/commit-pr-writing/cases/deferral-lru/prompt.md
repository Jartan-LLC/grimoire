Issue #41: `LRUCache(capacity=2)` keeps three items before it evicts anything. Fix the off-by-one with a
test and commit. Expiring entries after a time-to-live is a different feature request, #42, so don't add
that here.
