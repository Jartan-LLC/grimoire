const test = require("node:test");
const assert = require("node:assert");
const { ConsoleChannel } = require("../src/console");

test("console channel writes the text with its priority", async () => {
  const lines = [];
  const channel = new ConsoleChannel((line) => lines.push(line));
  const result = await channel.send({ text: "disk full", priority: "high" });
  assert.deepStrictEqual(result, { ok: true, id: "console-1" });
  assert.deepStrictEqual(lines, ["[high] disk full"]);
});
