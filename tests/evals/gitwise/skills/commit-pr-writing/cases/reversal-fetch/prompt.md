Fetching the pages one at a time on this branch takes minutes. Change `fetch_all` to fetch them
concurrently, at most 4 at a time (a thread pool is fine), keep results in input order, keep the tests
passing, and commit. The branch is already pushed.
