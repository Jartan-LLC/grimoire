import assert from "node:assert/strict";
import test from "node:test";
import { cartTotals, subtotalCents } from "../src/cart.js";

const lines = [
  { sku: "mug", unitCents: 850, quantity: 2 },
  { sku: "tea", unitCents: 450, quantity: 1 },
];

test("the subtotal sums the lines", () => {
  assert.equal(subtotalCents(lines), 2150);
});

test("totals without a coupon", () => {
  assert.deepEqual(cartTotals(lines, "GB"), {
    netCents: 2150,
    discountCents: 0,
    vatCents: 430,
    totalCents: 2580,
  });
});

test("a fixed coupon comes off before VAT", () => {
  assert.equal(cartTotals(lines, "GB", { kind: "fixed", cents: 500 }).totalCents, 1980);
});
