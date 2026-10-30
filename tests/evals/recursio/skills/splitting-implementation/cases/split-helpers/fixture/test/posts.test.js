import assert from "node:assert/strict";
import test from "node:test";
import { archivePages } from "../src/archive.js";
import { frontPage, makePost } from "../src/posts.js";

const a = makePost({ title: "first post", date: "2026-01-05" }, "Hello.\n\nMore.");
const b = makePost({ title: "the end of winter", date: "2026-03-02" }, "Spring.");

test("makePost fills in the slug and summary", () => {
  assert.equal(a.slug, "first-post");
  assert.equal(a.summary, "Hello.");
});

test("the front page is newest first", () => {
  assert.deepEqual(frontPage([a, b]).map((p) => p.slug), ["the-end-of-winter", "first-post"]);
});

test("the archive groups by month", () => {
  assert.deepEqual(archivePages([a, b], 10), [
    { month: "2026-03", page: 1, titles: ["The End of Winter"] },
    { month: "2026-01", page: 1, titles: ["First Post"] },
  ]);
});
