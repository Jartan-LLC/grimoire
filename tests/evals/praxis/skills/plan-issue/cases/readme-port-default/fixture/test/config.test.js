const test = require("node:test");
const assert = require("node:assert");
const { port } = require("../src/config");

test("PORT wins over the default", () => {
  assert.strictEqual(port({ PORT: "4000" }), 4000);
  assert.strictEqual(port({}), 3000);
});
