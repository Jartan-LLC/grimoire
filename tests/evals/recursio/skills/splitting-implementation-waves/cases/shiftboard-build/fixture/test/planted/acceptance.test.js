// Planted acceptance tests: one or two basic checks per module and two for the command.
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { main } from "../../src/cli.js";
import { bradford, entitlement, request, taken } from "../../src/leave.js";
import { RotaError, employee, leave, shift } from "../../src/model.js";
import { overtime, payslip, shiftPay } from "../../src/pay.js";
import { check, cover } from "../../src/rota.js";

const ANN = employee({ id: "ann", name: "Ann", role: "nurse", contractHours: 37, hourlyCents: 2000, startDate: "2025-01-06" });
const BOB = employee({ id: "bob", name: "Bob", role: "carer", contractHours: 40, hourlyCents: 1500, startDate: "2024-05-01" });
const CARL = employee({ id: "carl", name: "Carl", role: "cook", contractHours: 30, hourlyCents: 1400, startDate: "2026-07-01" });

const on = (who, start, end, role) => shift({ employee: who, start, end, role });
const pairs = (problems) => problems.map((p) => [p.shift, p.kind]);

test("check finds each kind of fault in order", () => {
  const shifts = [
    on("ann", "2026-03-02T07:00", "2026-03-02T15:00", "nurse"),
    on("ann", "2026-03-02T22:00", "2026-03-03T08:00", "nurse"),
    on("bob", "2026-03-02T08:00", "2026-03-02T21:00", "carer"),
    on("zed", "2026-03-02T08:00", "2026-03-02T12:00", "cook"),
    on("bob", "2026-03-02T20:00", "2026-03-02T23:00", "nurse"),
    on("ann", "2026-03-04T07:00", "2026-03-04T06:00", "nurse"),
  ];
  const problems = check(shifts, [ANN, BOB]);
  assert.deepEqual(pairs(problems), [[1, "rest"], [2, "length"], [3, "unknown"], [4, "role"], [4, "overlap"], [5, "times"]]);
  assert.equal(problems[0].detail, "rest of 7.0 h");
  assert.equal(problems[3].detail, "carer on a nurse shift");
});

test("weekly hours and hourly cover", () => {
  const week = ["02", "03", "04", "05", "06"].map((d) => on("ann", `2026-03-${d}T08:00`, `2026-03-${d}T18:00`, "nurse"));
  const problems = check(week, [ANN]);
  assert.deepEqual(problems, [{ shift: 4, kind: "weekly", detail: "50.0 h in the week of 2026-03-02" }]);
  const gaps = cover([week[0], on("bob", "2026-03-01T22:00", "2026-03-02T10:00", "carer")], "2026-03-02", { nurse: 1, carer: 1 });
  assert.equal(gaps.length, 28);
  assert.deepEqual(gaps[0], { hour: 0, role: "nurse", have: 0, need: 1 });
  assert.deepEqual(gaps.filter((g) => g.hour === 18).map((g) => g.role), ["carer", "nurse"]);
});

test("premiums by the minute, the highest only, and weekly overtime", () => {
  const late = on("ann", "2026-03-06T20:00", "2026-03-07T02:00", "nurse");
  assert.equal(shiftPay(late, ANN), 15000);
  assert.equal(shiftPay(late, ANN, new Set(["2026-03-07"])), 17000);
  const week = ["02", "03", "04", "05", "06"].map((d) => on("ann", `2026-03-${d}T08:00`, `2026-03-${d}T16:00`, "nurse"));
  assert.equal(overtime([...week, on("bob", "2026-03-02T08:00", "2026-03-02T16:00", "carer")], ANN), 3000);
  assert.deepEqual(payslip(week, ANN, "2026-03-02", "2026-03-08"), { minutes: 2400, gross: 80000, overtime: 3000, total: 83000 });
});

test("entitlement, leave taken, requests and the Bradford factor", () => {
  assert.equal(entitlement(ANN, 2026), 12432);
  assert.equal(entitlement(CARL, 2026), 5081);
  const leaves = [
    leave({ employee: "ann", from: "2026-03-05", to: "2026-03-10", kind: "annual" }),
    leave({ employee: "ann", from: "2025-12-29", to: "2026-01-02", kind: "annual" }),
    leave({ employee: "bob", from: "2026-03-05", to: "2026-03-06", kind: "annual" }),
  ];
  assert.equal(taken(leaves, ANN, 2026), 2664);
  const wanted = leave({ employee: "ann", from: "2026-03-10", to: "2026-03-11", kind: "annual" });
  assert.throws(() => request(leaves, ANN, wanted, 2026), RotaError);
  const long = leave({ employee: "ann", from: "2026-04-01", to: "2026-12-31", kind: "annual" });
  assert.throws(() => request(leaves, ANN, long, 2026), RotaError);
  const fine = leave({ employee: "ann", from: "2026-04-06", to: "2026-04-07", kind: "annual" });
  assert.equal(request(leaves, ANN, fine, 2026).length, 4);
  const sick = [
    leave({ employee: "ann", from: "2025-03-01", to: "2025-03-03", kind: "sick" }),
    leave({ employee: "ann", from: "2025-06-02", to: "2025-06-04", kind: "sick" }),
    leave({ employee: "ann", from: "2026-02-27", to: "2026-03-12", kind: "sick" }),
  ];
  assert.equal(bradford(sick, ANN, "2026-03-10"), 60);
});

function files(contents) {
  const dir = mkdtempSync(join(tmpdir(), "shiftboard-"));
  return Object.entries(contents).map(([name, text]) => {
    writeFileSync(join(dir, name), text);
    return join(dir, name);
  });
}

function run(argv) {
  const out = [];
  const err = [];
  const code = main(argv, { out: { write: (t) => out.push(t) }, err: { write: (t) => err.push(t) } });
  return { code, out: out.join("").split("\n").filter(Boolean), err: err.join("") };
}

const STAFF = "id,name,role,contract_hours,hourly_cents,start_date\nann,Ann,nurse,37,2000,2025-01-06\nbob,Bob,carer,40,1500,2024-05-01\n";

test("the check command numbers problems from 1 and exits 1", () => {
  const [staff, rota] = files({
    "staff.csv": STAFF,
    "rota.csv": "employee,start,end,role\nann,2026-03-02T07:00,2026-03-02T15:00,nurse\nann,2026-03-02T22:00,2026-03-03T08:00,nurse\n",
  });
  assert.deepEqual(run(["check", staff, rota]), { code: 1, out: ["shift 2: rest: rest of 7.0 h"], err: "" });
});

test("the pay and leave commands print their figures", () => {
  const [staff, rota, away] = files({
    "staff.csv": STAFF,
    "rota.csv": "employee,start,end,role\nann,2026-03-06T20:00,2026-03-07T02:00,nurse\n",
    "leave.csv": "employee,from,to,kind\nann,2026-03-05,2026-03-10,annual\n",
  });
  const pay = run(["pay", staff, rota, "--employee", "ann", "--from", "2026-03-01", "--to", "2026-03-31"]);
  assert.deepEqual(pay, { code: 0, out: ["minutes 360", "gross 150.00", "overtime 0.00", "total 150.00"], err: "" });
  const left = run(["leave", staff, away, "--employee", "ann", "--year", "2026"]);
  assert.deepEqual(left, { code: 0, out: ["entitlement 207.20", "taken 29.60", "balance 177.60"], err: "" });
  assert.equal(run(["leave", staff, away, "--employee", "nobody", "--year", "2026"]).code, 2);
});
