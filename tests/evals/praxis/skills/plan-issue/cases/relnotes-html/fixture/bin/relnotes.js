#!/usr/bin/env node
const { findRelease } = require("../src/releases");
const { renderText } = require("../src/text");

const version = process.argv[2];
if (!version) {
  console.error("usage: relnotes <version>");
  process.exit(2);
}
console.log(renderText(findRelease(process.env.RELNOTES_FILE || "releases.json", version)));
