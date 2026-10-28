const test = require("node:test");
const assert = require("node:assert");
const path = require("node:path");
const { findRelease } = require("../src/releases");
const { renderText } = require("../src/text");

test("groups changes by section", () => {
  const release = findRelease(path.join(__dirname, "..", "releases.json"), "2.3.0");
  assert.deepStrictEqual(release.sections.map((s) => s.title), ["Added", "Fixed"]);
});

test("plain text lists each change", () => {
  const release = { version: "1.0.0", date: "2026-01-02", sections: [{ title: "Fixed", items: ["A bug"] }] };
  assert.strictEqual(renderText(release), "Release 1.0.0 (2026-01-02)\n\nFixed:\n  - A bug");
});
