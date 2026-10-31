const test = require("node:test");
const assert = require("node:assert");
const { plurality } = require("../src/plurality");

test("plurality picks the most first preferences", () => {
  assert.strictEqual(plurality([["a", "b"], ["b", "a"], ["b"]]), "b");
});
