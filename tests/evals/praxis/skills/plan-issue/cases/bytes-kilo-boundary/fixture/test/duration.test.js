const test = require("node:test");
const assert = require("node:assert");
const { formatDuration } = require("../src/duration");

test("minutes and seconds", () => {
  assert.strictEqual(formatDuration(125), "2m 5s");
});

test("hours and minutes", () => {
  assert.strictEqual(formatDuration(3720), "1h 2m");
});
