const test = require("node:test");
const assert = require("node:assert");
const { slugify } = require("../src/slug");

test("joins words with hyphens", () => {
  assert.strictEqual(slugify("Hello, World!"), "hello-world");
});

test("drops accents", () => {
  assert.strictEqual(slugify("Cr\u00e8me br\u00fbl\u00e9e"), "creme-brulee");
});
