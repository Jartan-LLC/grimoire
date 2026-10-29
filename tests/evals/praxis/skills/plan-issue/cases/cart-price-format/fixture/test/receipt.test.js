const test = require("node:test");
const assert = require("node:assert");
const { receiptText } = require("../src/receipt");

test("prices in dollars with thousands separators", () => {
  const text = receiptText({ id: "A17", items: [{ name: "Espresso machine", qty: 1, unitCents: 123450 }] });
  assert.match(text, /Total\s+\$1,234\.50$/);
});
