const test = require("node:test");
const assert = require("node:assert");
const members = require("../src/members");
const { signup } = require("../src/signup");

test.beforeEach(() => members.reset());

test("signs up a new member", () => {
  const result = signup({ name: "Alex", email: "Alex@Example.com" });
  assert.strictEqual(result.status, 201);
  assert.strictEqual(result.member.email, "alex@example.com");
});

test("refuses a taken email", () => {
  signup({ name: "Alex", email: "alex@example.com" });
  assert.strictEqual(signup({ name: "Sam", email: "alex@example.com" }).status, 409);
});
