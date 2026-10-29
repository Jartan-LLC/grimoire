# pastebox

The team's pastebin: a small HTTP server that keeps pastes in memory.

- Node 20 or later, no dependencies.
- `npm test` runs the tests. Production runs one `node src/server.js` behind nginx, which passes
  the client address in `X-Real-IP`.
