const fs = require("node:fs");
const path = require("node:path");

// Every Markdown page under `dir`, as { file, text }.
function pages(dir = "docs") {
  return fs
    .readdirSync(dir, { recursive: true })
    .filter((f) => f.endsWith(".md"))
    .map((f) => ({ file: path.join(dir, f), text: fs.readFileSync(path.join(dir, f), "utf8") }));
}

module.exports = { pages };
