# shorty

The marketing team's link shortener: `POST /links` makes a short code, `GET /<code>` redirects.

- Node 20 or later, no dependencies.
- The request handling is a plain function, `handle` in `src/app.js`, so tests call it directly.
- `npm test` runs the tests.
