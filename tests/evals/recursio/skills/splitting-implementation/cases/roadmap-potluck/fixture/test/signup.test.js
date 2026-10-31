import assert from "node:assert/strict";
import test from "node:test";

import { cancel, signUp } from "../src/signup.js";

test("a guest signs up once", () => {
  const sheet = signUp({ guests: [] }, { name: "Ana", dish: "lentil soup", course: "starter" });
  assert.equal(sheet.guests.length, 1);
  assert.throws(() => signUp(sheet, { name: "Ana", dish: "bread", course: "side" }), /already/);
});

test("cancelling frees the guest's place", () => {
  const sheet = { guests: [{ name: "Bo", dish: "tiramisu", course: "dessert" }] };
  assert.deepEqual(cancel(sheet, "Bo").guests, []);
});
