import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { loadConfig } from "../src/load.js";

test("loadConfig migrates what it reads", () => {
  const path = join(mkdtempSync(join(tmpdir(), "stashd-")), "stashd.json");
  writeFileSync(path, JSON.stringify({ version: 1, target: "s3://b", keep: 2 }));
  assert.deepEqual(loadConfig(path), { version: 3, target: "s3://b", keepDays: 2, schedule: "daily" });
});
