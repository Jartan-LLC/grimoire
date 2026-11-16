#!/usr/bin/env node
const fs = require("node:fs");
const { parse, pick } = require("../src/columns");

const [file] = process.argv.slice(2);
if (!file) {
  console.error("usage: colcut <file.csv>");
  process.exit(2);
}
for (const row of parse(fs.readFileSync(file, "utf8"))) {
  console.log(pick(row, [0]).join(","));
}
