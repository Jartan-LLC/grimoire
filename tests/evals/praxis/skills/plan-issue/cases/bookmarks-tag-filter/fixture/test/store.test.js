const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const store = require("../src/store");

test("add then load", (t, done) => {
  const file = path.join(fs.mkdtempSync(path.join(os.tmpdir(), "marks-")), "marks.json");
  store.add(file, { url: "https://example.com", tags: ["reading"] }, (err) => {
    assert.ifError(err);
    store.load(file, (err2, marks) => {
      assert.ifError(err2);
      assert.deepStrictEqual(marks, [{ url: "https://example.com", tags: ["reading"] }]);
      done();
    });
  });
});
