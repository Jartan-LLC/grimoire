#!/usr/bin/env node
const fs = require("node:fs");
const { readEntries, totals } = require("../src/report");

const [command, file = "worklog.csv"] = process.argv.slice(2);
if (command !== "report") {
  console.error("usage: worklog report [file]");
  process.exit(2);
}
const entries = readEntries(fs.readFileSync(file, "utf8"));
for (const [project, hours] of Object.entries(totals(entries))) {
  console.log(`${project.padEnd(12)} ${hours.toFixed(1)}`);
}
