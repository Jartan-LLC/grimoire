// Links live in one JSON file, read and rewritten whole on every change.
// TODO: two requests at once can lose a write here; move to SQLite before we grow.
const fs = require("node:fs");

const file = () => process.env.SHORTY_FILE || "links.json";

function load() {
  return fs.existsSync(file()) ? JSON.parse(fs.readFileSync(file(), "utf8")) : {};
}

function get(code) {
  return load()[code];
}

function put(code, link) {
  const links = load();
  links[code] = link;
  fs.writeFileSync(file(), JSON.stringify(links, null, 2));
}

module.exports = { get, put };
