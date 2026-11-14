const test = require("node:test");
const assert = require("node:assert");
const { formatBookmark } = require("../src/format");

test("prints tags in brackets", () => {
  assert.strictEqual(formatBookmark(3, { url: "https://a.example", tags: ["x", "y"] }), "  3 https://a.example [x, y]");
});

test("no tags, no brackets", () => {
  assert.strictEqual(formatBookmark(1, { url: "https://b.example", tags: [] }), "  1 https://b.example");
});
