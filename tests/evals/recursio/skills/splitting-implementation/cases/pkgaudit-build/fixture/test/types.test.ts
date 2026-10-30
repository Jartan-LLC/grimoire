import assert from "node:assert/strict";
import test from "node:test";

import { AuditError, SEVERITIES, type Severity } from "../src/types.ts";

test("severities run from most to least severe", () => {
  assert.deepEqual(SEVERITIES, ["critical", "high", "moderate", "low", "info"]);
  const worst: Severity = SEVERITIES[0];
  assert.equal(worst, "critical");
});

test("an AuditError names the file it is about", () => {
  const err = new AuditError("lockfile v1 is not supported", "package-lock.json");
  assert.ok(err instanceof Error);
  assert.equal(err.name, "AuditError");
  assert.equal(err.file, "package-lock.json");
});

test("an AuditError may have no file", () => {
  assert.equal(new AuditError("bad range").file, null);
});
