import assert from "node:assert/strict";
import test from "node:test";
import { LATEST, migrate } from "../src/migrate.js";

const v1 = { version: 1, source: "/home/ada", target: "s3://backups/ada", keep: 7, exclude: "*.tmp, node_modules" };

test("a version 1 config comes up to the latest shape", () => {
  assert.equal(LATEST, 3);
  assert.deepEqual(migrate(v1), {
    version: 3,
    source: "/home/ada",
    target: "s3://backups/ada",
    keepDays: 7,
    exclude: "*.tmp, node_modules",
    schedule: "daily",
  });
});

test("a config with no version is version 1", () => {
  const { version, ...unversioned } = v1;
  assert.deepEqual(migrate(unversioned), migrate(v1));
});

test("only the migrations above the config's version run", () => {
  const v2 = { version: 2, target: "s3://b", keepDays: 3, schedule: "hourly" };
  assert.deepEqual(migrate(v2), { version: 3, target: "s3://b", keepDays: 3, schedule: "hourly" });
});

test("the input is left alone", () => {
  const copy = structuredClone(v1);
  migrate(v1);
  assert.deepEqual(v1, copy);
});

test("a newer or broken version is an error", () => {
  assert.throws(() => migrate({ version: 99 }), /newer than this stashd/);
  assert.throws(() => migrate({ version: "2" }), /bad config version/);
});
