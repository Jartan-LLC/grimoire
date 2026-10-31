import assert from "node:assert/strict";
import test from "node:test";
import { orgRepos, repoStars } from "../src/github.js";
import { fetchJson } from "../src/http.js";
import { json, stubFetch } from "./stub-fetch.js";

test("repoStars reads the star count", async (t) => {
  const stub = stubFetch(() => json({ stargazers_count: 42 }));
  t.after(stub.restore);
  assert.equal(await repoStars("acme", "widgets"), 42);
  assert.deepEqual(stub.urls, ["https://api.github.com/repos/acme/widgets"]);
});

test("orgRepos lists names in the order the API gives them", async (t) => {
  const stub = stubFetch(() => json([{ name: "b" }, { name: "a" }]));
  t.after(stub.restore);
  assert.deepEqual(await orgRepos("acme"), ["b", "a"]);
  assert.deepEqual(await fetchJson("https://api.github.com/orgs/acme/repos"), [{ name: "b" }, { name: "a" }]);
});
