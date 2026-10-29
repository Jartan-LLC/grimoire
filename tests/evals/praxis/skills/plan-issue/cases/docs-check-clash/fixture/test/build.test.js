const test = require("node:test");
const assert = require("node:assert");
const { toHtml } = require("../src/build");

test("turns a heading and a link into HTML", () => {
  assert.strictEqual(toHtml("# Hi\nSee [x](commands.md)"), '<h1>Hi</h1>\n<p>See <a href="commands.html">x</a></p>');
});
