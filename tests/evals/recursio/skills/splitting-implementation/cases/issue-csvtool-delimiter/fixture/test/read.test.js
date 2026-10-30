import assert from "node:assert/strict";
import test from "node:test";
import { parseCsv } from "../src/read.js";

test("rows and fields", () => {
  assert.deepEqual(parseCsv("a,b\n1,2\n"), [["a", "b"], ["1", "2"]]);
});

test("quoted fields keep commas, newlines and doubled quotes", () => {
  assert.deepEqual(parseCsv('name,note\n"Lin, A","said ""hi""\nthen left"\n'), [
    ["name", "note"],
    ["Lin, A", 'said "hi"\nthen left'],
  ]);
});

test("CRLF line ends and an empty last field", () => {
  assert.deepEqual(parseCsv("a,b\r\n1,\r\n"), [["a", "b"], ["1", ""]]);
});
