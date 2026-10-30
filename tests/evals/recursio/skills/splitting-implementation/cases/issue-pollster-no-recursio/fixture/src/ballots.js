const fs = require("node:fs");

// Each ballot is an array of candidates, most preferred first.
function readBallots(path) {
  return fs
    .readFileSync(path, "utf8")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => line.split(",").map((c) => c.trim()));
}

module.exports = { readBallots };
