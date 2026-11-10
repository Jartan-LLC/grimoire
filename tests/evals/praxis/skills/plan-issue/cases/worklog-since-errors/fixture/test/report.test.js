const test = require("node:test");
const assert = require("node:assert");
const { readEntries, totals } = require("../src/report");

test("totals sums hours per project", () => {
  const entries = readEntries("date,project,hours\n2026-10-01,site,2\n2026-10-02,site,1.5\n");
  assert.deepStrictEqual(totals(entries), { site: 3.5 });
});
