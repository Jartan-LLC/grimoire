const test = require("node:test");
const assert = require("node:assert");
const { parseArgs } = require("../src/args");

test("reads the command, its text and a tag", () => {
  const args = parseArgs(["add", "Buy", "milk", "--tag", "shop"]);
  assert.deepStrictEqual(args.positional, ["Buy", "milk"]);
  assert.strictEqual(args.tag, "shop");
});

test("reads --tag=value", () => {
  assert.strictEqual(parseArgs(["add", "x", "--tag=home"]).tag, "home");
});
