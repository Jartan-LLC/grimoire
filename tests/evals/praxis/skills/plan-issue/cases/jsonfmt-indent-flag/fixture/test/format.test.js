const test = require("node:test");
const assert = require("node:assert");
const { format } = require("../src/format");

test("two-space indent and a trailing newline", () => {
  assert.strictEqual(format('{"a":1}'), '{\n  "a": 1\n}\n');
});

test("sorts keys on request", () => {
  assert.strictEqual(format('{"b":1,"a":2}', { sort: true }), '{\n  "a": 2,\n  "b": 1\n}\n');
});
