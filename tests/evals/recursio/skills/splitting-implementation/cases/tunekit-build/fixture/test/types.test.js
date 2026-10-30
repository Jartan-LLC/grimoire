import assert from "node:assert/strict";
import test from "node:test";

import { MAJOR_KEY_FIFTHS, MODE_FIFTHS_OFFSET, TICKS_PER_QUARTER, TuneError } from "../src/types.js";

test("triplet eighths and sixteenths are whole ticks", () => {
  assert.equal(TICKS_PER_QUARTER % 3, 0);
  assert.equal(Number.isInteger(TICKS_PER_QUARTER / 4), true);
});

test("a mode's offset moves the signature from the major key", () => {
  assert.equal(MAJOR_KEY_FIFTHS.A + MODE_FIFTHS_OFFSET.dorian, 1);
  assert.equal(MAJOR_KEY_FIFTHS.E + MODE_FIFTHS_OFFSET.minor, 1);
});

test("a TuneError says where the input went wrong", () => {
  const err = new TuneError("unclosed chord", 4, 17);
  assert.equal(err.name, "TuneError");
  assert.deepEqual([err.line, err.column], [4, 17]);
});
