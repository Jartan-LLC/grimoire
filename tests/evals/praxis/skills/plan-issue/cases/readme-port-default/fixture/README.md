# mockapi

Put one JSON file per route in a folder (`mocks/users.json` answers `GET /users`) and run:

```bash
npx mockapi mocks/
```

The server listens on `http://localhost:8080` unless you set `PORT`.

A file may hold a `_status` key to answer with that status code instead of 200.
