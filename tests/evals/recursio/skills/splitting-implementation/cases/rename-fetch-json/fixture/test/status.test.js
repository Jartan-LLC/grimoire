import assert from "node:assert/strict";
import test from "node:test";
import { fetchJson } from "../src/http.js";
import { isUp } from "../src/status.js";
import { json, stubFetch } from "./stub-fetch.js";

test("a service saying ok is up", async (t) => {
  const stub = stubFetch(() => json({ status: "ok" }));
  t.after(stub.restore);
  assert.equal(await isUp("https://svc.test"), true);
  assert.deepEqual(await fetchJson("https://svc.test/health"), { status: "ok" });
});

test("a 503 is down", async (t) => {
  const stub = stubFetch(() => new Response("busy", { status: 503 }));
  t.after(stub.restore);
  assert.equal(await isUp("https://svc.test"), false);
});
