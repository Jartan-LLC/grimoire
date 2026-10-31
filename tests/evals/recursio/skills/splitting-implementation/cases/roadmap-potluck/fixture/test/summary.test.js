import assert from "node:assert/strict";
import test from "node:test";

import { missingCourses } from "../src/summary.js";

test("courses with no dish are missing", () => {
  const sheet = {
    guests: [
      { name: "Ana", dish: "lentil soup", course: "starter" },
      { name: "Bo", dish: "tiramisu", course: "dessert" },
    ],
  };
  assert.deepEqual(missingCourses(sheet), ["main", "side", "drinks"]);
});
