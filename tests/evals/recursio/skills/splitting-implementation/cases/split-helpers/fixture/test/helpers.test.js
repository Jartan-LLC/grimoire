import assert from "node:assert/strict";
import test from "node:test";
import { addDays, chunk, groupBy, isoDate, parseDate, slugify, titleCase, truncate, uniqueBy } from "../src/helpers.js";

test("strings", () => {
  assert.equal(slugify("Cafe au lait, s'il vous plait!"), "cafe-au-lait-s-il-vous-plait");
  assert.equal(truncate("the quick brown fox", 13), "the quick...");
  assert.equal(titleCase("war and peace in the city"), "War and Peace in the City");
});

test("arrays", () => {
  assert.deepEqual(chunk([1, 2, 3, 4, 5], 2), [[1, 2], [3, 4], [5]]);
  assert.deepEqual(uniqueBy(["a1", "b1", "a2"], (s) => s[0]), ["a1", "b1"]);
  assert.deepEqual([...groupBy(["ax", "by", "az"], (s) => s[0]).keys()], ["a", "b"]);
});

test("dates", () => {
  assert.equal(isoDate(addDays(parseDate("2026-02-27"), 2)), "2026-03-01");
  assert.throws(() => parseDate("27/02/2026"), /not a date/);
});
