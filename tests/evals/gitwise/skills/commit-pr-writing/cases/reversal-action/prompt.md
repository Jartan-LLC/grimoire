On this branch, `get_user` raises `LookupError` for an unknown id, and the last commit told callers to
catch it. That made every caller wrap it in try/except. Change `get_user` to return `None` for an unknown
id instead, update the test, and commit. The branch is already pushed, and two other teams read its
commit messages to update their callers.
