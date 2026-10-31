#!/usr/bin/env node
const { readBallots } = require("../src/ballots");
const { plurality } = require("../src/plurality");

const [file] = process.argv.slice(2);
if (!file) {
  console.error("usage: tally BALLOTS");
  process.exit(2);
}
console.log(plurality(readBallots(file)));
