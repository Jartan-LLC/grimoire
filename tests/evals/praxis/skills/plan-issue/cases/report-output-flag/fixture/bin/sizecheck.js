#!/usr/bin/env node
const { parseArgs } = require("node:util");
const { measure, parseSize } = require("../src/measure");
const report = require("../src/report");

const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: {
    budget: { type: "string", short: "b" },
    json: { type: "boolean" },
    open: { type: "boolean", short: "o" },
  },
});

const files = measure(positionals[0] || "dist");
const budget = values.budget ? parseSize(values.budget) : Infinity;
console.log(values.json ? report.json(files, budget) : report.table(files, budget));
if (values.open) report.openHtml(files);
process.exitCode = files.some((f) => f.gzip > budget) ? 1 : 0;
