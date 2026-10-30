const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { loadEvents } = require("../src/events");

test("events load oldest first", () => {
  const file = path.join(fs.mkdtempSync(path.join(os.tmpdir(), "ev-")), "events.json");
  fs.writeFileSync(file, JSON.stringify([
    { id: "2", title: "b", start: "2026-02-01T10:00:00Z", end: "2026-02-01T11:00:00Z", tags: [] },
    { id: "1", title: "a", start: "2026-01-01T10:00:00Z", end: "2026-01-01T11:00:00Z", tags: [] },
  ]));
  assert.deepStrictEqual(loadEvents(file).map((e) => e.id), ["1", "2"]);
});
