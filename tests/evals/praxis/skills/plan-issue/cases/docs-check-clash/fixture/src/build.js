const fs = require("node:fs");
const path = require("node:path");
const { pages } = require("./pages");

function toHtml(markdown) {
  return markdown
    .split("\n")
    .map((line) => (line.startsWith("# ") ? `<h1>${line.slice(2)}</h1>` : `<p>${line}</p>`))
    .join("\n")
    .replace(/\[([^\]]+)\]\(([^)]+)\.md\)/g, '<a href="$2.html">$1</a>');
}

function run() {
  for (const page of pages()) {
    const out = path.join("site", path.relative("docs", page.file).replace(/\.md$/, ".html"));
    fs.mkdirSync(path.dirname(out), { recursive: true });
    fs.writeFileSync(out, toHtml(page.text));
  }
}

module.exports = { toHtml, run };
