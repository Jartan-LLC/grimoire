import assert from "node:assert/strict";
import test from "node:test";

import { type Cue, DEFAULT_LIMITS, FORMATS } from "../src/types.ts";

test("subtool knows three formats", () => {
  assert.deepEqual(FORMATS, ["srt", "vtt", "ass"]);
});

test("the default limits allow two lines of 42 characters", () => {
  assert.equal(DEFAULT_LIMITS.maxLines, 2);
  assert.equal(DEFAULT_LIMITS.maxLineLength, 42);
  assert.equal(Object.isFrozen(DEFAULT_LIMITS), true);
});

test("a cue needs only times and lines", () => {
  const cue: Cue = { start: 1000, end: 2500, lines: ["<i>Hello.</i>"] };
  assert.equal(cue.end - cue.start, 1500);
  assert.equal(cue.position, undefined);
});
