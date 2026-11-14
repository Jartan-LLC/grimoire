const test = require("node:test");
const assert = require("node:assert");
const { parseAnswers, parseKey, gradeAll } = require("../src/grade");
const { formatTable } = require("../src/table");

const answers = parseAnswers("student,q1,q2,q3\nAmara,A,c,D\nJonas,B,C,D\n");
const key = parseKey("A\nC\nB\n");

test("marks each sheet against the key", () => {
  assert.deepStrictEqual(gradeAll(answers, key), [
    { student: "Amara", score: 2, outOf: 3 },
    { student: "Jonas", score: 1, outOf: 3 },
  ]);
});

test("prints one row per student", () => {
  assert.strictEqual(formatTable(gradeAll(answers, key)).split("\n")[1], "Amara    2/3");
});
