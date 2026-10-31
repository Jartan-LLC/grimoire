import assert from "node:assert/strict";
import test from "node:test";

import { isStandupDay, pastDeadline } from "../src/schedule.ts";
import { loadSettings } from "../src/settings.ts";

const settings = loadSettings("team.json", () => '{"timezone": "Europe/Berlin"}');

test("weekends are quiet", () => {
  assert.equal(isStandupDay(settings, new Date("2026-10-31T09:00:00Z")), false);
  assert.equal(isStandupDay(settings, new Date("2026-10-30T09:00:00Z")), true);
});

test("the deadline is read in the team's timezone", () => {
  assert.equal(pastDeadline(settings, new Date("2026-10-30T08:30:00Z")), false);
  assert.equal(pastDeadline(settings, new Date("2026-10-30T09:30:00Z")), true);
});
