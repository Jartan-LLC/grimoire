import assert from "node:assert/strict";
import test from "node:test";
import { cartTotals } from "../src/cart.js";
import { discountCents } from "../src/coupon.js";

test("a fixed coupon takes no more than the net", () => {
  assert.equal(discountCents({ kind: "fixed", cents: 5000 }, 2000, "GB"), 2000);
});

test("the minimum spend is checked against the shelf price", () => {
  const coupon = { kind: "fixed", cents: 500, minSpendCents: 3000 };
  assert.equal(discountCents(coupon, 2000, "GB"), 0);
  assert.equal(discountCents(coupon, 2500, "GB"), 500);
});

test("a percent coupon comes off the net, before VAT", () => {
  const coupon = { kind: "percent", percent: 10 };
  assert.equal(discountCents(coupon, 4000, "GB"), 400);
  const kettle = [{ sku: "kettle", unitCents: 4000, quantity: 1 }];
  assert.equal(cartTotals(kettle, "GB", coupon).totalCents, 4320);
});
