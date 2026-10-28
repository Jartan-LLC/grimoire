const test = require("node:test");
const assert = require("node:assert");
const { textColor } = require("../src/index");

test("white text on dark blue", () => {
  assert.strictEqual(textColor("#1e3a8a"), "#ffffff");
});

test("black text on yellow", () => {
  assert.strictEqual(textColor("#facc15"), "#000000");
});
