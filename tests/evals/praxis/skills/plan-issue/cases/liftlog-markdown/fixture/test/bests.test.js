const test = require("node:test");
const assert = require("node:assert");
const { personalBests } = require("../src/bests");
const sessions = require("../data/sample-log.json");

test("keeps the heaviest set of each lift", () => {
  const squat = personalBests(sessions).find((r) => r.lifter === "Ana" && r.lift === "Squat");
  assert.deepStrictEqual([squat.kg, squat.reps, squat.date], [85, 3, "2026-09-09"]);
});

test("breaks a tie on weight by reps", () => {
  const bench = personalBests(sessions).find((r) => r.lifter === "Ana" && r.lift === "Bench");
  assert.deepStrictEqual([bench.kg, bench.reps], [50, 6]);
});
