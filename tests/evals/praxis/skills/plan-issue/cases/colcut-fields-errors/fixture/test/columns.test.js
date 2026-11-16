const test = require("node:test");
const assert = require("node:assert");
const { parse, pick } = require("../src/columns");

test("pick returns the fields at the indexes, in order", () => {
  const [row] = parse("a,b,c\n");
  assert.deepStrictEqual(pick(row, [2, 0]), ["c", "a"]);
});
