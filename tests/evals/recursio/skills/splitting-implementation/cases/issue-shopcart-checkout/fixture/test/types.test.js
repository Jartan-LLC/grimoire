import assert from "node:assert/strict";
import test from "node:test";

import { ORDER_STATES, PROMOTION_KINDS, ShopError } from "../src/types.js";

test("an order starts placed and the usual path ends delivered", () => {
  assert.equal(ORDER_STATES[0], "placed");
  assert.equal(ORDER_STATES.indexOf("delivered"), 4);
});

test("pricing knows five kinds of promotion", () => {
  assert.deepEqual([...PROMOTION_KINDS].sort(), ["bundle", "buy_x_get_y", "fixed", "percent", "tier"]);
});

test("a shop error carries a stable code", () => {
  const err = new ShopError("invalid_transition", "cannot ship an order that is placed");
  assert.ok(err instanceof Error);
  assert.equal(err.code, "invalid_transition");
});
