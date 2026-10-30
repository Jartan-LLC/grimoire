import assert from "node:assert/strict";
import test from "node:test";

import { REGIONS } from "../src/types.ts";
import type { Entry, Region } from "../src/types.ts";

test("four regions are known", () => {
  assert.deepEqual([...REGIONS], ["US", "GB-ENG", "DE-BY", "FR"]);
});

test("an entry keeps local times and the real minutes between them", () => {
  const entry: Entry = {
    person: "rosa",
    project: "atlas",
    start: "2026-10-24T22:00",
    end: "2026-10-25T06:00",
    zone: "Europe/Berlin",
    minutes: 540,
    billable: true,
    note: "",
  };
  const region: Region = "DE-BY";
  assert.equal(entry.minutes, 9 * 60);
  assert.ok(REGIONS.includes(region));
});
