const test = require("node:test");
const assert = require("node:assert");
const { formatBytes } = require("../src/bytes");

test("small counts stay in bytes", () => {
  assert.strictEqual(formatBytes(512), "512 B");
});

test("larger counts get one decimal", () => {
  assert.strictEqual(formatBytes(1536), "1.5 KB");
  assert.strictEqual(formatBytes(5 * 1024 * 1024 + 1), "5.0 MB");
});
