const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { respond } = require("../src/routes");

test("answers from the matching file, with its status", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "mockapi-"));
  fs.writeFileSync(path.join(dir, "users.json"), JSON.stringify({ _status: 201, id: 1 }));
  assert.deepStrictEqual(respond(dir, "/users"), { status: 201, body: { id: 1 } });
  assert.strictEqual(respond(dir, "/nope").status, 404);
});
