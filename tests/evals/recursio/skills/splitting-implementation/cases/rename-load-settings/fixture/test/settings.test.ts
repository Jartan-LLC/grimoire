import assert from "node:assert/strict";
import test from "node:test";

import { loadSettings } from "../src/settings.ts";

test("missing fields take the defaults", () => {
  const settings = loadSettings("team.json", () => '{"members": ["ana", "bo"]}');
  assert.equal(settings.deadline, "10:00");
  assert.deepEqual(settings.members, ["ana", "bo"]);
});

test("a malformed deadline is refused", () => {
  assert.throws(() => loadSettings("team.json", () => '{"deadline": "9am"}'), /HH:MM/);
});
