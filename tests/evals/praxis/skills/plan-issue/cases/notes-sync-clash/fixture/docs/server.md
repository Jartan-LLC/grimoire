# Team notes server

The team server stores shared notes at `https://notes.internal.example`.

- `GET /notes` lists `{id, title, updated}` for every note on the server.
- `PUT /notes/<id>` creates or replaces a note; the body is `{title, text, updated}` as JSON.
- Every request sends `Authorization: Bearer <token>`.
