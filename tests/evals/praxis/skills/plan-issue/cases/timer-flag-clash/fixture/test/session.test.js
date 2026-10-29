const test = require("node:test");
const assert = require("node:assert");
const { countdown } = require("../src/session");

test("marks every five minutes", () => {
  assert.deepStrictEqual(countdown(25), [25, 20, 15, 10, 5]);
});
