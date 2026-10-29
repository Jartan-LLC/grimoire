#!/usr/bin/env node
const fs = require("node:fs");
const { personalBests } = require("../src/bests");

const [command, file] = process.argv.slice(2);
if (command !== "bests" || !file) {
  console.error("usage: liftlog bests <log.json>");
  process.exit(2);
}
const sessions = JSON.parse(fs.readFileSync(file, "utf8"));
const rows = personalBests(sessions);
const headers = ["Lifter", "Lift", "Kg", "Reps", "Date"];
const cells = rows.map((r) => [r.lifter, r.lift, String(r.kg), String(r.reps), r.date]);
const widths = headers.map((h, i) => Math.max(h.length, ...cells.map((c) => c[i].length)));
const line = (c) => c.map((v, i) => v.padEnd(widths[i])).join("  ").trimEnd();
console.log([line(headers), ...cells.map(line)].join("\n"));
