const test = require("node:test");
const assert = require("node:assert");
const { merge } = require("../src/merge");

const event = (uid) => `BEGIN:VEVENT\r\nUID:${uid}\r\nSUMMARY:x\r\nEND:VEVENT\r\n`;

test("keeps one copy of a repeated UID", () => {
  const out = merge([event("a") + event("b"), event("a")]);
  assert.strictEqual(out.match(/BEGIN:VEVENT/g).length, 2);
});
