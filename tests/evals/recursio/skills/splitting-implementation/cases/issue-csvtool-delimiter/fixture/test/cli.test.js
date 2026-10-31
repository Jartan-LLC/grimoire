import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { run } from "../src/cli.js";

function capture() {
  const out = { text: "", write(s) { this.text += s; } };
  const err = { text: "", write(s) { this.text += s; } };
  return { out, err, io: { stdout: out, stderr: err } };
}

function csvFile(text) {
  const path = join(mkdtempSync(join(tmpdir(), "csvtool-")), "data.csv");
  writeFileSync(path, text);
  return path;
}

test("cols prints the header", () => {
  const { out, io } = capture();
  assert.equal(run(["cols", csvFile("id,name\n1,Ada\n")], io), 0);
  assert.equal(out.text, "id\nname\n");
});

test("count leaves out the header", () => {
  const { out, io } = capture();
  assert.equal(run(["count", csvFile("id\n1\n2\n3\n")], io), 0);
  assert.equal(out.text, "3\n");
});

test("a missing file or command is reported", () => {
  const { err, io } = capture();
  assert.equal(run(["count", "/no/such/file.csv"], io), 1);
  assert.match(err.text, /cannot read \/no\/such\/file\.csv: ENOENT/);
  assert.equal(run(["sum"], io), 2);
});
