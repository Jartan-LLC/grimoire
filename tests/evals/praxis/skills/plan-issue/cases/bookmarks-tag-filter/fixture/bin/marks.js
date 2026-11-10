#!/usr/bin/env node
const { parseArgs } = require("node:util");
const store = require("../src/store");
const { formatBookmark } = require("../src/format");

const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: { tag: { type: "string", multiple: true } },
});
const [command, ...rest] = positionals;
const file = process.env.MARKS_FILE || `${process.env.HOME}/.marks.json`;

if (command === "add") {
  store.add(file, { url: rest[0], tags: values.tag || [] }, (err) => {
    if (err) throw err;
  });
} else if (command === "list") {
  store.load(file, (err, marks) => {
    if (err) throw err;
    marks.forEach((mark, i) => console.log(formatBookmark(i + 1, mark)));
  });
} else {
  console.error("usage: marks add <url> [--tag <tag>...] | marks list");
  process.exitCode = 2;
}
