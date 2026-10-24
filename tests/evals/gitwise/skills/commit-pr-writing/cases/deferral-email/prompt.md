Re #88: `is_valid_email("ana+news@example.com")` says False, but plus-addressing is valid. Fix that, add a
test, commit. (Domains with non-ASCII letters are a separate question, #89; we haven't
decided whether to accept them yet.)
