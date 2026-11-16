// Rows are split on commas; quoted fields are not supported.
function parse(text) {
  return text.trim().split("\n").map((line) => line.split(","));
}

// The fields at the given 0-based indexes, in that order; a missing one is "".
function pick(row, indexes) {
  return indexes.map((i) => row[i] ?? "");
}

module.exports = { parse, pick };
