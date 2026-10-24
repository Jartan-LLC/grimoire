The last commit on this branch made `connect(timeout=...)` take milliseconds and told callers to pass
milliseconds. Every other function in the library takes seconds, so switch `connect` to seconds, update
the test, and commit. The branch is already pushed, and the other teams update their calls from its
commit messages.
