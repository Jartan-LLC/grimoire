#!/usr/bin/env node
const fs = require("node:fs");
const { monthlyRows } = require("../src/report");
const { renderTable } = require("../src/table");

const [file, month] = process.argv.slice(2);
if (!file || !month) {
  console.error("usage: salesreport <orders.json> <YYYY-MM>");
  process.exit(2);
}
const orders = JSON.parse(fs.readFileSync(file, "utf8"));
console.log(renderTable(monthlyRows(orders, month)));
