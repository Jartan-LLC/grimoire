const test = require("node:test");
const assert = require("node:assert");
const { permalink } = require("../src/permalink");

test("year and month from the publish date", () => {
  const post = { title: "Spring cleaning", published: "2026-04-03T09:00:00Z" };
  assert.strictEqual(permalink(post), "/2026/04/spring-cleaning/");
});
