const test = require("node:test");
const assert = require("node:assert");
const { server } = require("../src/server");

test("a paste can be posted and read back", async () => {
  await new Promise((resolve) => server.listen(0, resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  const posted = await fetch(`${base}/pastes`, { method: "POST", body: "hello" });
  assert.strictEqual(posted.status, 201);
  const { id } = await posted.json();
  const read = await fetch(`${base}/pastes/${id}`);
  assert.strictEqual((await read.json()).text, "hello");
  server.close();
});
