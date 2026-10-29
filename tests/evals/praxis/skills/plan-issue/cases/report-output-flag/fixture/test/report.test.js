const test = require("node:test");
const assert = require("node:assert");
const report = require("../src/report");

test("json report carries the budget and the files", () => {
  const out = JSON.parse(report.json([{ file: "a.js", raw: 10, gzip: 30 }], 51200));
  assert.strictEqual(out.budget, 51200);
  assert.strictEqual(out.files[0].file, "a.js");
});
