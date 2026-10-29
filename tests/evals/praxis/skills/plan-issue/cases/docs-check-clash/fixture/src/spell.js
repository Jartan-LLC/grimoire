const fs = require("node:fs");
const { pages } = require("./pages");

const COMMON = new Set(["the", "a", "to", "of", "and", "in", "on", "it", "then", "run", "see", "site", "docs"]);

// Words that are neither common nor in the project's word list, with the page they are on.
function misspelled(texts, known) {
  const found = [];
  for (const { file, text } of texts) {
    for (const word of text.toLowerCase().match(/[a-z]+/g) || []) {
      if (word.length > 3 && !COMMON.has(word) && !known.has(word)) found.push({ file, word });
    }
  }
  return found;
}

function run(argv) {
  const i = argv.indexOf("--words");
  const known = new Set(i >= 0 ? fs.readFileSync(argv[i + 1], "utf8").split(/\s+/) : []);
  const found = misspelled(pages(), known);
  for (const { file, word } of found) console.log(`${file}: ${word}`);
  return found.length ? 1 : 0;
}

module.exports = { misspelled, run };
