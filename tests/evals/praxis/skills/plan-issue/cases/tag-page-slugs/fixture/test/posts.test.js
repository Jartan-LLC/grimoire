const test = require("node:test");
const assert = require("node:assert");
const { parsePost, postPath } = require("../src/posts");

test("reads the front matter", () => {
  const post = parsePost("---\ntitle: Hello\ndate: 2026-01-02\ntags: Node.js, Coffee\n---\nBody\n");
  assert.deepStrictEqual(post.tags, ["Node.js", "Coffee"]);
});

test("addresses are lowercase ASCII", () => {
  assert.strictEqual(postPath({ title: "Jalape\u00f1o salsa: notes" }), "/posts/jalapeno-salsa-notes/");
});
