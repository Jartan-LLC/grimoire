const test = require("node:test");
const assert = require("node:assert");
const { addItem } = require("../src/commands/add");
const { formatItem } = require("../src/commands/list");

test("numbers new items after the highest id", () => {
  const items = addItem([{ id: 4, text: "a", tag: null, done: true }], "b", null);
  assert.strictEqual(items[1].id, 5);
});

test("formats an open tagged item", () => {
  assert.strictEqual(formatItem({ id: 7, text: "Call", tag: "home", done: false }), "  7 [ ] Call #home");
});
