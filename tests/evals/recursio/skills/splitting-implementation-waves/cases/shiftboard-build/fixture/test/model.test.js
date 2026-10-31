import assert from "node:assert/strict";
import { test } from "node:test";

import { RotaError, employee, formatDay, parseDay, parseStamp, shift } from "../src/model.js";

test("times and days count from 1970 and refuse what is not one", () => {
  assert.equal(parseStamp("1970-01-02T01:30"), 1530);
  assert.equal(formatDay(parseDay("2026-03-02")), "2026-03-02");
  assert.throws(() => parseStamp("2026-02-30T08:00"), RotaError);
  assert.throws(() => parseDay("2026-3-2"), RotaError);
});

test("records are frozen and checked", () => {
  const ann = employee({ id: "ann", name: "Ann", role: "nurse", contractHours: 37, hourlyCents: 2000, startDate: "2025-01-06" });
  assert.ok(Object.isFrozen(ann));
  assert.throws(() => shift({ employee: "ann", start: "2026-03-02T08:00", end: "2026-03-02T16:00", role: "porter" }), RotaError);
});
