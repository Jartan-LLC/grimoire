# Report: path traversal in file downloads

Received privately on 2026-11-06.

`GET /files/..%2F..%2Fetc%2Fpasswd` returns the server's `/etc/passwd`. Any file the
service user can read is exposed. The reporter will publish in 30 days.
