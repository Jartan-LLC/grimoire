const test = require("node:test");
const assert = require("node:assert");
const { wrap } = require("../src/wrap");

test("breaks at spaces", () => {
  assert.deepStrictEqual(wrap("one two three four", 8), ["one two", "three", "four"]);
});

test("a long word keeps a line of its own", () => {
  assert.deepStrictEqual(wrap("supercalifragilistic is long", 10), ["supercalifragilistic", "is long"]);
});
