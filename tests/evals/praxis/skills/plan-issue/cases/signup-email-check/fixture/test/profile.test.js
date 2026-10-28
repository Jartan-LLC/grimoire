const test = require("node:test");
const assert = require("node:assert");
const members = require("../src/members");
const { updateProfile } = require("../src/profile");

test.beforeEach(() => members.reset());

test("rejects an invalid email", () => {
  const result = updateProfile({ id: "1", name: "Alex", email: "a@b.co" }, { email: "alex@" });
  assert.strictEqual(result.status, 400);
});

test("saves a valid email", () => {
  const result = updateProfile({ id: "1", name: "Alex", email: "a@b.co" }, { email: "alex@example.com" });
  assert.strictEqual(result.member.email, "alex@example.com");
});
