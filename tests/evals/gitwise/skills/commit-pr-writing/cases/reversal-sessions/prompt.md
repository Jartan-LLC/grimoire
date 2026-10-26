Cookie-stored sessions on this branch can't be revoked, which security needs. Switch to server-side
sessions: keep a dict of session id -> user in `sessions/__init__.py` and put only the id in the
cookie. Keep the tests passing and commit. The branch is already pushed.
