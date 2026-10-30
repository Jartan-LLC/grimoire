import assert from "node:assert/strict";
import test from "node:test";
import { formatBytes } from "../src/format.js";

test("bytes stay whole", () => {
  assert.equal(formatBytes(512), "512 B");
});

test("larger sizes get one decimal", () => {
  assert.equal(formatBytes(1536), "1.5 KiB");
  assert.equal(formatBytes(3 * 1024 ** 3), "3.0 GiB");
});
