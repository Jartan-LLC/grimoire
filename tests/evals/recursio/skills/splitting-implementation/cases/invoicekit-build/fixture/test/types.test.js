import assert from "node:assert/strict";
import test from "node:test";

import { CURRENCY_DIGITS, InvoiceError, TAX_CATEGORIES } from "../src/types.js";

test("minor units follow the currency", () => {
  assert.equal(CURRENCY_DIGITS.EUR, 2);
  assert.equal(CURRENCY_DIGITS.JPY, 0);
  assert.equal(CURRENCY_DIGITS.BHD, 3);
});

test("the currency table cannot be changed", () => {
  assert.equal(Object.isFrozen(CURRENCY_DIGITS), true);
  assert.equal(Object.isFrozen(TAX_CATEGORIES), true);
});

test("an InvoiceError is an Error with its own name", () => {
  const err = new InvoiceError("no USD rate on or before 2026-01-01");
  assert.ok(err instanceof Error);
  assert.equal(err.name, "InvoiceError");
});
