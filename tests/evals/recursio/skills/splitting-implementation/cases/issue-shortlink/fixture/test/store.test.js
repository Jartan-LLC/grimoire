const test = require("node:test");
const assert = require("node:assert");
const { MemoryStore } = require("../src/store");

test("a created link resolves to its url", () => {
  const store = new MemoryStore();
  const code = store.create("https://example.com/a");
  assert.strictEqual(store.resolve(code), "https://example.com/a");
  assert.strictEqual(store.resolve("nope"), null);
});
