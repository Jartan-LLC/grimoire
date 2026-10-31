import assert from "node:assert/strict";
import test from "node:test";

import { buildDigest } from "../src/digest.ts";
import { missing } from "../src/nudge.ts";
import { loadSettings } from "../src/settings.ts";

const settings = loadSettings("team.json", () => '{"members": ["ana", "bo", "cy"]}');
const notes = [
  { author: "bo", text: "reviewing the billing PR" },
  { author: "ana", text: "on call" },
  { author: "bo", text: "then the release notes" },
];

test("the digest lists every member in order", () => {
  assert.equal(
    buildDigest(settings, notes),
    [
      "Standup digest for #standup",
      "*ana*: on call",
      "*bo*: reviewing the billing PR / then the release notes",
      "*cy*: -",
    ].join("\n"),
  );
});

test("members without notes are nudged", () => {
  assert.deepEqual(missing(settings, notes), ["cy"]);
});
