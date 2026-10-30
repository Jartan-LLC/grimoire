import assert from "node:assert/strict";
import test from "node:test";
import { HttpError, fetchJson } from "../src/http.js";
import { json, stubFetch } from "./stub-fetch.js";

test("fetchJson parses a 200", async (t) => {
  const stub = stubFetch(() => json({ ok: 1 }));
  t.after(stub.restore);
  assert.deepEqual(await fetchJson("https://x.test/a"), { ok: 1 });
});

test("fetchJson gives null for a 204", async (t) => {
  const stub = stubFetch(() => new Response(null, { status: 204 }));
  t.after(stub.restore);
  assert.equal(await fetchJson("https://x.test/a"), null);
});

test("fetchJson throws HttpError on a non-2xx answer", async (t) => {
  const stub = stubFetch(() => new Response("gone", { status: 404 }));
  t.after(stub.restore);
  await assert.rejects(fetchJson("https://x.test/a"), (error) => {
    assert.ok(error instanceof HttpError);
    assert.equal(error.status, 404);
    assert.equal(error.body, "gone");
    return true;
  });
});
