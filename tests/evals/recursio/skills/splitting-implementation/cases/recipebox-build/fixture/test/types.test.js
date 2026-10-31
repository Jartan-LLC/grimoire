import assert from "node:assert/strict";
import test from "node:test";

import { UNITS } from "../src/types.js";

test("every unit measures volume, mass or a count", () => {
  for (const [name, unit] of Object.entries(UNITS)) {
    assert.ok(["volume", "mass", "count"].includes(unit.dimension), name);
  }
});

test("the unit table cannot be changed", () => {
  assert.ok(Object.isFrozen(UNITS));
  assert.ok(Object.isFrozen(UNITS.cup));
});

test("unit names are lower-case keys", () => {
  for (const name of Object.keys(UNITS)) assert.equal(name, name.toLowerCase());
});

test("a cup is sixteen tablespoons", () => {
  assert.ok(Math.abs(UNITS.cup.base - 16 * UNITS.tbsp.base) < 1e-9);
});
