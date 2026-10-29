const test = require("node:test");
const assert = require("node:assert");
const { cartTotal, cartSummary } = require("../src/cart");

const cart = { items: [{ name: "Tea", qty: 2, unitCents: 450 }, { name: "Honey", qty: 1, unitCents: 799 }] };

test("total in cents", () => {
  assert.strictEqual(cartTotal(cart), 1699);
});

test("counts items", () => {
  assert.match(cartSummary(cart).footer, /^3 items\./);
});
