import assert from "node:assert/strict";
import test from "node:test";

import { LEVELS } from "../src/types.ts";
import type { LogRecord } from "../src/types.ts";

test("levels run from least to most severe", () => {
  assert.equal(LEVELS[0], "debug");
  assert.equal(LEVELS.at(-1), "critical");
  assert.ok(LEVELS.indexOf("error") > LEVELS.indexOf("warning"));
});

test("a record needs only its time, source, level, message and fields", () => {
  const record: LogRecord = {
    at: Date.UTC(2026, 9, 11, 22, 14, 15),
    source: "api",
    level: "info",
    message: "GET /health HTTP/1.1",
    fields: {},
  };
  assert.equal(record.status, undefined);
  assert.equal(new Date(record.at).toISOString(), "2026-10-11T22:14:15.000Z");
});
