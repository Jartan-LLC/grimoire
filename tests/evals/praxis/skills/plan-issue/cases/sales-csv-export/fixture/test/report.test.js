const test = require("node:test");
const assert = require("node:assert");
const { monthlyRows } = require("../src/report");
const { renderTable } = require("../src/table");
const orders = require("../data/sample-orders.json");

test("sums one month by product, biggest first", () => {
  const rows = monthlyRows(orders, "2026-09");
  assert.deepStrictEqual(rows.map((r) => [r.product, r.units, r.cents]), [
    ["Mug, blue", 2, 2400],
    ["Tea towel", 1, 800],
  ]);
});

test("renders a header row and one line per product", () => {
  const lines = renderTable(monthlyRows(orders, "2026-09")).split("\n");
  assert.strictEqual(lines.length, 4);
  assert.match(lines[0], /^Product/);
});
