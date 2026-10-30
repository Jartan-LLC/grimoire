const test = require("node:test");
const assert = require("node:assert");
const { MemorySink } = require("../src/memory-sink");

test("flush moves pending metrics", async () => {
  const sink = new MemorySink();
  sink.record({ name: "hits", type: "counter", value: 1, tags: {} });
  await sink.flush();
  assert.strictEqual(sink.flushed.length, 1);
  assert.strictEqual(sink.pending.length, 0);
});
