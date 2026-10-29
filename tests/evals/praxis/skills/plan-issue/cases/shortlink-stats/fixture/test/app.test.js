const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

process.env.SHORTY_FILE = path.join(fs.mkdtempSync(path.join(os.tmpdir(), "shorty-")), "links.json");
const { handle } = require("../src/app");

test("a new link redirects", () => {
  const { status, body } = handle("POST", "/links", { url: "https://example.com/spring-sale" });
  assert.strictEqual(status, 201);
  const res = handle("GET", `/${body.code}`, {});
  assert.strictEqual(res.status, 302);
  assert.strictEqual(res.headers.location, "https://example.com/spring-sale");
});

test("an unknown code is a 404", () => {
  assert.strictEqual(handle("GET", "/nope", {}).status, 404);
});

test("only http(s) urls", () => {
  assert.strictEqual(handle("POST", "/links", { url: "ftp://x" }).status, 400);
});
