const test = require("node:test");
const assert = require("node:assert");
const { misspelled } = require("../src/spell");

test("reports unknown words and skips known ones", () => {
  const found = misspelled([{ file: "a.md", text: "Run pkgdoc then zorbly" }], new Set(["pkgdoc"]));
  assert.deepStrictEqual(found, [{ file: "a.md", word: "zorbly" }]);
});
