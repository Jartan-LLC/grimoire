import assert from "node:assert/strict";
import test from "node:test";
import { grossCents, vatCents } from "../src/tax.js";

test("VAT is rounded to the cent", () => {
  assert.equal(vatCents(1000, "GB"), 200);
  assert.equal(vatCents(1999, "DE"), 380);
});

test("the shelf price adds VAT", () => {
  assert.equal(grossCents(2500, "IE"), 3075);
});

test("an unknown country is an error", () => {
  assert.throws(() => vatCents(100, "XX"), /no VAT rate for XX/);
});
