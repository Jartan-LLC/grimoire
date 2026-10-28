const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { measure, parseSize } = require("../src/measure");

test("parses sizes with units", () => {
  assert.strictEqual(parseSize("50kb"), 51200);
  assert.strictEqual(parseSize("900"), 900);
});

test("measures every file, largest first", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "sizecheck-"));
  fs.writeFileSync(path.join(dir, "a.js"), "x".repeat(10));
  fs.writeFileSync(path.join(dir, "b.js"), "0123456789abcdefghij".repeat(50));
  assert.deepStrictEqual(measure(dir).map((f) => f.file), ["b.js", "a.js"]);
});
