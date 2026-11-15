#!/usr/bin/env node
const fs = require("node:fs");
const { merge } = require("../src/merge");

const texts = process.argv.slice(2).map((path) => fs.readFileSync(path, "utf8"));
process.stdout.write(merge(texts));
